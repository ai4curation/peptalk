"""A REST-like API over the annotator (``pip install 'peptalk[server]'``; run with ``peptalk serve``).

Endpoints (OpenAPI docs at ``/docs`` and ``/openapi.json``):

- ``POST /annotate``: annotate a few sequences and wait for the answers.
- ``POST /jobs``: start a larger job, live calls in the background (``mode: live``) or one provider batch
  (``mode: batch``, half price, within 24 hours); returns a job id.
- ``GET /jobs/{job_id}``: a job's status, and its answers once done. Polling a batch job collects it when the
  provider has finished.
- ``GET /sequences/{seq_md5}``: every stored answer for a sequence, by the MD5 of its upper-case residues.
- ``GET /health``, ``GET /models``, ``GET /tasks``.

Provider API keys come from the server's environment. The server has no authentication of its own: bind it to
localhost (the default) or put it behind something that has.
"""

from __future__ import annotations

import datetime
import json
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from peptalk import __version__, batch
from peptalk.annotator import Annotator, Question, build_questions, new_annotation
from peptalk.fasta import SequenceRecord, clean_sequence, parse_fasta
from peptalk.headers import PROFILES
from peptalk.pricing import PRICES, Price
from peptalk.providers import PROVIDERS, installed, provider_for
from peptalk.providers.base import Provider
from peptalk.report import totals
from peptalk.schema import Annotation
from peptalk.store import Store
from peptalk.templates import CONTEXTS, DEFAULT_CONTEXT, PAYLOADS, TEMPLATES

DEFAULT_MODEL = "claude-fable-5-2"
DEFAULT_EFFORT = "high"

ProviderFactory = Callable[[str, str | None], Provider]


class SequenceIn(BaseModel):
    id: str = Field(examples=["Q2PAY3"])
    sequence: str = Field(examples=["MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQ"])
    description: str = ""


class AnnotateRequest(BaseModel):
    """Sequences (as a list, or as FASTA text) and what to ask of them."""

    sequences: list[SequenceIn] = Field(default_factory=list)
    fasta: str | None = Field(default=None, description="FASTA text, as an alternative to `sequences`.")
    tasks: list[str] = Field(default=["features"], description=f"Any of: {', '.join(TEMPLATES)}.")
    model: str = DEFAULT_MODEL
    effort: str = DEFAULT_EFFORT
    provider: str | None = Field(
        default=None, description=f"One of {', '.join(PROVIDERS)}; default from the model name."
    )
    context: str = Field(default=DEFAULT_CONTEXT, description="; ".join(f"{k}: {v}" for k, v in CONTEXTS.items()))
    header_profile: str = Field(default="auto", description=f"FASTA header profile: auto, {', '.join(PROFILES)}.")
    params: dict[str, str] = Field(default_factory=dict, description="Placeholders of an ask-* template.")
    payload: list[str] = Field(default_factory=list, description=f"Extra answer keys: {', '.join(PAYLOADS)}.")
    structured: bool = Field(default=False, description="Constrain replies to the task's JSON Schema (opt-in).")
    shuffle_control: bool = False
    reuse: bool = Field(default=True, description="Reuse stored answers instead of asking again.")
    verify_input: bool = Field(default=True, description="Check that each call sent nothing besides the prompt.")

    @model_validator(mode="after")
    def _check(self) -> AnnotateRequest:
        bad = [t for t in self.tasks if t not in TEMPLATES]
        if bad:
            raise ValueError(f"unknown task(s) {', '.join(bad)}; choose from {', '.join(TEMPLATES)}")
        if not self.sequences and not self.fasta:
            raise ValueError("give `sequences` or `fasta`")
        if self.context not in CONTEXTS:
            raise ValueError(f"unknown context {self.context!r}; choose from {', '.join(CONTEXTS)}")
        bad = [p for p in self.payload if p not in PAYLOADS]
        if bad:
            raise ValueError(f"unknown payload {', '.join(bad)}; choose from {', '.join(PAYLOADS)}")
        return self

    def questions(self) -> list[Question]:
        return build_questions(
            self.records(), self.tasks, self.shuffle_control, self.context, self.params, self.payload
        )

    def records(self) -> list[SequenceRecord]:
        recs = [
            SequenceRecord(id=s.id, description=s.description, sequence=clean_sequence(s.sequence))
            for s in self.sequences
        ]
        return recs + (parse_fasta(self.fasta, self.header_profile) if self.fasta else [])


class JobRequest(AnnotateRequest):
    mode: Literal["live", "batch"] = Field(
        default="live", description="live: calls in the background; batch: provider batch API."
    )


class AnnotateResponse(BaseModel):
    annotations: list[Annotation]
    totals: dict[str, Any]


class Job(BaseModel):
    job_id: str
    kind: Literal["live", "batch"]
    status: Literal["queued", "running", "submitted", "done", "failed"]
    created_at: str
    updated_at: str
    error: str | None = None
    batch_id: str | None = None
    batch_state: str | None = None
    questions: int = 0
    annotations: list[Annotation] | None = None


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def default_factory(model: str, provider: str | None) -> Provider:
    return provider_for(model, provider)


def create_app(
    store: Store,
    provider_factory: ProviderFactory = default_factory,
    max_sync_questions: int = 20,
    prices: dict[str, Price] | None = None,
    workers: int = 2,
) -> FastAPI:
    """Build the API around a store. ``provider_factory(model, provider)`` makes providers (tests pass fakes)."""
    app = FastAPI(
        title="peptalk",
        version=__version__,
        description="Protein annotation from sequence alone by direct, single-shot LLM API calls.",
    )
    executor = ThreadPoolExecutor(workers)

    def make_provider(req: AnnotateRequest) -> Provider:
        try:
            return provider_factory(req.model, req.provider)
        except (ImportError, ValueError) as e:
            raise HTTPException(400, str(e)) from e

    def records_of(req: AnnotateRequest) -> list[SequenceRecord]:
        try:
            return req.records()
        except ValueError as e:
            raise HTTPException(422, str(e)) from e

    def annotator(req: AnnotateRequest, provider: Provider) -> Annotator:
        return Annotator(
            provider,
            req.model,
            req.effort,
            store=store,
            prices=prices,
            verify_input=req.verify_input,
            reuse=req.reuse,
            context=req.context,
            structured=req.structured,
            payload=req.payload,
        )

    def save(job: Job, request: JobRequest, manifest: str | None = None, uids: list[str] | None = None) -> None:
        job.updated_at = _now()
        row = job.model_dump(include={"job_id", "kind", "status", "error", "created_at", "updated_at"})
        row.update(request=request.model_dump_json(), manifest=manifest, uids=json.dumps(uids or []))
        store.save_job(row)

    def load(job_id: str) -> tuple[Job, JobRequest, dict]:
        row = store.load_job(job_id)
        if row is None:
            raise HTTPException(404, f"no job {job_id}")
        request = JobRequest.model_validate_json(row["request"])
        manifest = json.loads(row["manifest"]) if row["manifest"] else None
        job = Job(
            job_id=row["job_id"],
            kind=row["kind"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            error=row["error"],
            batch_id=manifest["batch_id"] if manifest else None,
        )
        return job, request, row

    def run_live(job: Job, request: JobRequest, provider: Provider, recs: list[SequenceRecord]) -> None:
        job.status = "running"
        save(job, request)
        out = annotator(request, provider).run(request.questions())
        job.status = "done"
        save(job, request, uids=[a.uid for a in out])

    def record_failure(job: Job, request: JobRequest, future: Future) -> None:
        """Mark a live job failed if its thread raised (provider errors are recorded per call instead)."""
        if (e := future.exception()) is not None:
            job.status, job.error = "failed", f"{type(e).__name__}: {e}"
            save(job, request)

    @app.get("/health", summary="Service status")
    def health() -> dict[str, Any]:
        return {"status": "ok", "version": __version__, "records": store.count()}

    @app.get("/models", summary="Providers, defaults and built-in prices")
    def models() -> dict[str, Any]:
        return {
            "default_model": DEFAULT_MODEL,
            "default_effort": DEFAULT_EFFORT,
            "providers": installed(),
            "prices_usd_per_million_tokens": {m: p.model_dump() for m, p in {**PRICES, **(prices or {})}.items()},
        }

    @app.get("/tasks", summary="Tasks and their prompt versions")
    def tasks() -> list[dict[str, Any]]:
        return [
            {"name": t.name, "version": t.version, "source": t.source, "summary": t.summary, "params": t.params}
            for t in TEMPLATES.values()
        ]

    @app.get("/tasks/{name}/schema", summary="JSON Schema of a task's answer")
    def task_schema(name: str) -> dict[str, Any]:
        if name not in TEMPLATES:
            raise HTTPException(404, f"no task {name}")
        return TEMPLATES[name].json_schema()

    @app.post("/annotate", response_model=AnnotateResponse, summary="Annotate a few sequences and wait")
    def annotate(req: AnnotateRequest) -> AnnotateResponse:
        recs = records_of(req)
        n = len(recs) * len(req.tasks) * (2 if req.shuffle_control else 1)
        if n > max_sync_questions:
            raise HTTPException(413, f"{n} questions; at most {max_sync_questions} here. POST /jobs instead.")
        try:
            questions = req.questions()
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        out = annotator(req, make_provider(req)).run(questions)
        return AnnotateResponse(annotations=out, totals=totals(out))

    @app.post("/jobs", response_model=Job, status_code=202, summary="Start a background or batch job")
    def start_job(req: JobRequest) -> Job:
        recs = records_of(req)
        provider = make_provider(req)
        try:
            questions = req.questions()
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
        job = Job(
            job_id=uuid.uuid4().hex,
            kind=req.mode,
            status="queued",
            created_at=_now(),
            updated_at=_now(),
            questions=len(questions),
        )
        if req.mode == "live":
            save(job, req)
            future = executor.submit(run_live, job, req, provider, recs)
            future.add_done_callback(lambda f: record_failure(job, req, f))
            return job
        reused: list[str] = []
        todo = []
        for q in questions:
            hit = (
                store.lookup(new_annotation(q, provider, req.model, req.effort, req.structured)) if req.reuse else None
            )
            if hit is None:
                todo.append(q)
            else:
                reused.append(hit.uid)
        if not todo:
            job.status = "done"
            save(job, req, uids=reused)
            return job
        m = batch.submit(
            provider, todo, req.model, req.effort, verify_input=req.verify_input, structured=req.structured
        )
        job.status, job.batch_id = "submitted", m.batch_id
        save(job, req, manifest=m.model_dump_json(), uids=reused)
        return job

    @app.get("/jobs/{job_id}", response_model=Job, summary="Job status, and answers once done")
    def get_job(job_id: str) -> Job:
        job, request, row = load(job_id)
        uids = json.loads(row["uids"])
        if job.kind == "batch" and job.status == "submitted":
            provider = make_provider(request)
            manifest = batch.BatchManifest.model_validate_json(row["manifest"])
            state = provider.batch_status(manifest.batch_id)
            job.batch_state = state.state
            if state.done:
                out = batch.collect(provider, manifest, store=store, prices=prices)
                uids += [a.uid for a in out]
                job.status = "done"
                save(job, request, manifest=row["manifest"], uids=uids)
        job.questions = len(request.questions())
        if job.status == "done":
            job.annotations = store.by_uids(uids)
        return job

    @app.get("/sequences/{seq_md5}", response_model=list[Annotation], summary="Stored answers for a sequence")
    def by_sequence(
        seq_md5: str,
        task: str | None = Query(default=None, description="Only this task."),
        model: str | None = Query(default=None, description="Only this model."),
    ) -> list[Annotation]:
        where, params = ["seq_md5 = ?"], [seq_md5.lower()]
        if task:
            where.append("task = ?")
            params.append(task)
        if model:
            where.append("model = ?")
            params.append(model)
        return list(store.records(" AND ".join(where), params))

    return app
