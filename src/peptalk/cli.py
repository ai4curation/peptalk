"""The ``peptalk`` command line."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from peptalk import __version__
from peptalk.annotator import Annotator, build_questions, new_annotation
from peptalk.claims import ClaimsError, read_claims
from peptalk.exchange import annotated_fasta, export_records, import_jsonl, to_gff3, to_parquet
from peptalk.fasta import SequenceRecord, format_fasta, parse_fasta, shuffle_sequence
from peptalk.headers import PROFILES
from peptalk.pricing import load_prices
from peptalk.providers import PROVIDERS, provider_for
from peptalk.providers.base import Provider
from peptalk.report import dumps_json, read_jsonl, totals_line, write_jsonl, write_tsv
from peptalk.schema import Annotation
from peptalk.store import DEFAULT_KEY, KEY_FIELDS, Store, default_db_path
from peptalk.templates import CONTEXTS, DEFAULT_CONTEXT, PAYLOADS, TEMPLATES, params_table

EPILOG = """Examples:

  peptalk annotate proteins.fasta -t features -t active-site --shuffle-control -o results.jsonl

  peptalk annotate - -m claude-opus-5-5 -f tsv < one.fasta

  peptalk batch submit proteins.fasta --manifest m.json   (then: peptalk batch status m.json; peptalk batch collect m.json)

  peptalk log      peptalk export --parquet calls.parquet      peptalk serve
"""

app = typer.Typer(
    help="Annotate protein sequences with a frontier language model, from sequence alone.",
    epilog=EPILOG,
    no_args_is_help=True,
    rich_markup_mode="markdown",
)
batch_app = typer.Typer(help="Provider batch APIs: half price, results within 24 hours.", no_args_is_help=True)
app.add_typer(batch_app, name="batch")
templates_app = typer.Typer(
    help="Template schemas: generate a template's Pydantic and JSON Schema from its LinkML schema.yaml.",
    no_args_is_help=True,
)
app.add_typer(templates_app, name="templates")

DEFAULT_MODEL = "claude-fable-5-2"
DEFAULT_EFFORT = "high"
DEFAULT_KEY_TEXT = ",".join(DEFAULT_KEY)


class Format(str, Enum):
    jsonl = "jsonl"
    json = "json"
    tsv = "tsv"


FastaArg = Annotated[Path, typer.Argument(help="FASTA file, or - for standard input.", allow_dash=True)]
TaskOpt = Annotated[
    list[str] | None,
    typer.Option(
        "--task",
        "-t",
        help=f"Task to run; repeatable. One of: {', '.join(TEMPLATES)} [default: features].",
        rich_help_panel="Question",
    ),
]
ModelOpt = Annotated[
    str, typer.Option("--model", "-m", help="Model id, as the provider names it.", rich_help_panel="Model")
]
EffortOpt = Annotated[
    str,
    typer.Option("--effort", "-e", help="Effort / thinking level (provider's own labels).", rich_help_panel="Model"),
]
ProviderOpt = Annotated[
    str | None,
    typer.Option(help=f"One of {', '.join(PROVIDERS)} [default: from the model name].", rich_help_panel="Model"),
]
ContextOpt = Annotated[
    str,
    typer.Option(
        "--context",
        "-c",
        help="How much of each FASTA header the model sees: "
        + "; ".join(f"{k}: {v}" for k, v in CONTEXTS.items())
        + ". Use blind for validation studies.",
        rich_help_panel="Question",
    ),
]
ProfileOpt = Annotated[
    str,
    typer.Option(
        "--header-profile",
        help=f"How to parse FASTA headers: auto, {', '.join(PROFILES)}.",
        rich_help_panel="Question",
    ),
]
ParamOpt = Annotated[
    list[str] | None,
    typer.Option(
        "--param",
        "-p",
        help="KEY=VALUE for an ask template's placeholders (repeatable), e.g. -p term=GO:0004672.",
        rich_help_panel="Question",
    ),
]
PayloadOpt = Annotated[
    list[str] | None,
    typer.Option(
        "--with",
        "-w",
        help=f"Extra answer keys (repeatable or comma-separated): {', '.join(PAYLOADS)}. They cost tokens and can "
        "change the answer; fix the choice for an evaluation run.",
        rich_help_panel="Question",
    ),
]
ConcurrencyOpt = Annotated[int, typer.Option(help="Questions asked at once.", rich_help_panel="Model")]
StructuredOpt = Annotated[
    bool,
    typer.Option(
        "--structured/--no-structured",
        help="Ask the provider to constrain replies to the task's JSON Schema (opt-in: changes the protocol).",
        rich_help_panel="Model",
    ),
]
ShuffleOpt = Annotated[
    bool,
    typer.Option(
        "--shuffle-control/--no-shuffle-control",
        help="Also ask each task of a shuffled copy.",
        rich_help_panel="Question",
    ),
]
DbOpt = Annotated[
    Path | None,
    typer.Option(
        "--db",
        help="SQLite log and cache [default: ~/.local/share/peptalk/peptalk.db].",
        rich_help_panel="Store, cache and cost",
    ),
]
ReuseOpt = Annotated[
    bool,
    typer.Option(
        "--reuse/--no-reuse",
        help="Reuse a stored answer instead of asking again.",
        rich_help_panel="Store, cache and cost",
    ),
]
KeyOpt = Annotated[
    str,
    typer.Option(
        help=f"Comma-separated fields a stored answer must match to be reused; from {', '.join(KEY_FIELDS)}.",
        rich_help_panel="Store, cache and cost",
    ),
]
VerifyOpt = Annotated[
    bool,
    typer.Option(
        "--verify-input/--no-verify-input",
        help="Count each prompt's tokens first and check the call sent nothing else.",
        rich_help_panel="Model",
    ),
]
PricesOpt = Annotated[
    Path | None,
    typer.Option(
        help="JSON file of extra prices per model ($ per million tokens).", rich_help_panel="Store, cache and cost"
    ),
]
OutOpt = Annotated[
    Path | None, typer.Option("--output", "-o", help="Write here instead of standard output.", rich_help_panel="Output")
]
FormatOpt = Annotated[
    Format,
    typer.Option(
        "--format", "-f", help="jsonl: one full record per line; tsv: a summary table.", rich_help_panel="Output"
    ),
]
MaxTokensOpt = Annotated[
    int, typer.Option(help="Anthropic only: output limit per answer, thinking included.", rich_help_panel="Model")
]


def _read_records(fasta: Path, profile: str = "auto") -> list[SequenceRecord]:
    text = sys.stdin.read() if str(fasta) == "-" else fasta.read_text()
    try:
        return parse_fasta(text, profile)
    except ValueError as e:
        raise typer.BadParameter(str(e)) from e


def _params(items: list[str] | None) -> dict[str, str]:
    out = {}
    for item in items or []:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise typer.BadParameter(f"--param takes KEY=VALUE, not {item!r}")
        out[key.strip()] = value.strip()
    return out


def _payload(items: list[str] | None) -> list[str]:
    names = [n.strip() for item in items or [] for n in item.split(",") if n.strip()]
    bad = [n for n in names if n not in PAYLOADS]
    if bad:
        raise typer.BadParameter(f"unknown --with {', '.join(bad)}; choose from {', '.join(PAYLOADS)}")
    return names


def _check_context(context: str) -> str:
    if context not in CONTEXTS:
        raise typer.BadParameter(f"unknown context {context!r}; choose from {', '.join(CONTEXTS)}")
    return context


def _check_tasks(tasks: list[str] | None) -> list[str]:
    tasks = tasks or ["features"]
    bad = [t for t in tasks if t not in TEMPLATES]
    if bad:
        raise typer.BadParameter(f"unknown task(s) {', '.join(bad)}; choose from {', '.join(TEMPLATES)}")
    return tasks


def _store(db: Path | None, key: str = DEFAULT_KEY_TEXT) -> Store:
    try:
        return Store(db or default_db_path(), key=[f.strip() for f in key.split(",") if f.strip()])
    except ValueError as e:
        raise typer.BadParameter(str(e)) from e


def _provider(name: str | None, model: str, fallback: bool = False, max_tokens: int = 64_000) -> Provider:
    try:
        return provider_for(model, name, fallback, max_tokens)
    except (ImportError, ValueError) as e:
        raise typer.BadParameter(str(e)) from e


def _write(annotations: list[Annotation], fmt: Format, output: Path | None) -> None:
    fh = output.open("w") if output else sys.stdout
    if fmt is Format.jsonl:
        write_jsonl(annotations, fh)  # type: ignore[arg-type]
    elif fmt is Format.json:
        fh.write(dumps_json(annotations) + "\n")
    else:
        write_tsv(annotations, fh)  # type: ignore[arg-type]
    if output:
        fh.close()


def _version(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool, typer.Option("--version", callback=_version, is_eager=True, help="Show the version.")
    ] = False,
) -> None:
    pass


@app.command()
def annotate(
    fasta: FastaArg,
    task: TaskOpt = None,
    model: ModelOpt = DEFAULT_MODEL,
    effort: EffortOpt = DEFAULT_EFFORT,
    provider: ProviderOpt = None,
    context: ContextOpt = DEFAULT_CONTEXT,
    header_profile: ProfileOpt = "auto",
    param: ParamOpt = None,
    payload: PayloadOpt = None,
    shuffle_control: ShuffleOpt = False,
    structured: StructuredOpt = False,
    output: OutOpt = None,
    fmt: FormatOpt = Format.jsonl,
    db: DbOpt = None,
    log: Annotated[
        bool,
        typer.Option(
            "--log/--no-log",
            help="Log calls in the store (and reuse from it).",
            rich_help_panel="Store, cache and cost",
        ),
    ] = True,
    reuse: ReuseOpt = True,
    cache_key: KeyOpt = DEFAULT_KEY_TEXT,
    verify_input: VerifyOpt = True,
    prices: PricesOpt = None,
    concurrency: ConcurrencyOpt = 4,
    fallback: Annotated[
        bool, typer.Option(help="Anthropic only: let another model answer a declined request.", rich_help_panel="Model")
    ] = False,
    max_tokens: MaxTokensOpt = 64_000,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="No progress or totals on standard error.", rich_help_panel="Output")
    ] = False,
) -> None:
    """Annotate every sequence in a FASTA file, one question per sequence and task.

    Each sequence is sent alone. How much of its FASTA header goes with it is set by --context.
    """
    records = _read_records(fasta, header_profile)
    tasks = _check_tasks(task)
    annotator = Annotator(
        _provider(provider, model, fallback, max_tokens),
        model=model,
        effort=effort,
        store=_store(db, cache_key) if log else None,
        prices=load_prices(prices) if prices else None,
        concurrency=concurrency,
        verify_input=verify_input,
        reuse=reuse,
        context=_check_context(context),
        structured=structured,
        payload=_payload(payload),
    )
    try:
        annotations = annotator.annotate(
            records, tasks, shuffle_control=shuffle_control, progress=_progress(quiet), params=_params(param)
        )
    except ValueError as e:  # a template parameter missing, or a payload the template cannot take
        raise typer.BadParameter(str(e)) from e
    _write(annotations, fmt, output)
    if not quiet:
        typer.echo(totals_line(annotations), err=True)


def _progress(quiet: bool) -> Callable[[Annotation], None] | None:
    def show(a: Annotation) -> None:
        how = "reused" if a.cached else (a.error or a.confidence)
        typer.echo(f"{a.id}\t{a.task}\t{a.condition}\t{how}", err=True)

    return None if quiet else show


@app.command()
def ask(
    fasta: FastaArg,
    claims: Annotated[
        Path,
        typer.Option(
            help="Claims file: YAML (.yaml) to write by hand, or TSV/CSV for bulk input. See docs/claims.md; "
            "'peptalk tasks --ask' lists the templates and their parameters."
        ),
    ],
    model: ModelOpt = DEFAULT_MODEL,
    effort: EffortOpt = DEFAULT_EFFORT,
    provider: ProviderOpt = None,
    context: ContextOpt = DEFAULT_CONTEXT,
    header_profile: ProfileOpt = "auto",
    payload: PayloadOpt = None,
    shuffle_control: ShuffleOpt = False,
    structured: StructuredOpt = False,
    output: OutOpt = None,
    fmt: FormatOpt = Format.jsonl,
    db: DbOpt = None,
    reuse: ReuseOpt = True,
    verify_input: VerifyOpt = True,
    prices: PricesOpt = None,
    concurrency: ConcurrencyOpt = 4,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="No progress or totals on standard error.", rich_help_panel="Output")
    ] = False,
) -> None:
    """Check specific claims, one per call: each claim gets a verdict (yes, no or uncertain).

    Example (examples/claims.yaml in the repository):

        proteins:
          - id: Q2PAY3_wt
            claims:
              - task: ask-catalytic-residue
                params: {position: 436, residue: D}
                expected: yes

    'expected' and 'note' are optional and never sent to the model; with 'expected', the totals report how many
    verdicts agree.
    """
    records = _read_records(fasta, header_profile)
    try:
        claim_list = read_claims(claims)
    except (ClaimsError, OSError) as e:
        typer.echo(f"Error in claims file:\n{e}", err=True)
        raise typer.Exit(2) from e
    annotator = Annotator(
        _provider(provider, model),
        model=model,
        effort=effort,
        store=_store(db),
        prices=load_prices(prices) if prices else None,
        concurrency=concurrency,
        verify_input=verify_input,
        reuse=reuse,
        context=_check_context(context),
        structured=structured,
        payload=_payload(payload),
    )
    try:
        annotations = annotator.check_claims(records, claim_list, shuffle_control, _progress(quiet))
    except (ValueError, KeyError) as e:
        raise typer.BadParameter(str(e)) from e
    _write(annotations, fmt, output)
    if not quiet:
        typer.echo(totals_line(annotations), err=True)


@app.command()
def summarize(
    results: Annotated[Path, typer.Argument(help="JSONL file written by 'annotate', 'batch collect' or 'export'.")],
    output: OutOpt = None,
) -> None:
    """Print a summary table (TSV) of saved results, and their totals on standard error."""
    annotations = read_jsonl(results)
    _write(annotations, Format.tsv, output)
    typer.echo(totals_line(annotations), err=True)


LOG_SQL = (
    "SELECT started_at, id, task, condition, provider, model, served_model, effort, confidence, input_tokens, "
    "output_tokens, thinking_tokens, round(cost_usd, 4) AS cost_usd, batch, error FROM calls "
    "ORDER BY started_at DESC LIMIT ?"
)


@app.command("log")
def show_log(
    db: DbOpt = None,
    sql: Annotated[str | None, typer.Option(help="Run this SQL on the 'calls' table instead (read-only).")] = None,
    limit: Annotated[int, typer.Option(help="Most recent calls to list.")] = 20,
) -> None:
    """List logged calls (TSV), or run a read-only SQL query on the log."""
    store = _store(db)
    cols, rows = store.query(sql) if sql else store.query(LOG_SQL, [limit])
    typer.echo("\t".join(cols))
    for row in rows:
        typer.echo("\t".join("" if v is None else str(v) for v in row))


@app.command("export")
def export_cmd(
    db: DbOpt = None,
    output: OutOpt = None,
    parquet: Annotated[
        Path | None, typer.Option(help="Write Parquet here instead of JSONL (needs the 'parquet' extra).")
    ] = None,
    gff3: Annotated[
        Path | None, typer.Option(help="Write GFF3 of the located features (domains, TM helices, residues) here.")
    ] = None,
    gff_seqid: Annotated[str, typer.Option(help="GFF3 sequence ids: 'id' (FASTA id) or 'md5'.")] = "id",
    real_only: Annotated[bool, typer.Option(help="Leave out the shuffled controls.")] = False,
) -> None:
    """Write every logged call: JSONL (to merge with 'peptalk import'), Parquet (to query) or GFF3 (features).

    Records carry the sequence, its MD5 (seq_md5) and the call's uid, so exports from different people
    merge without duplicates. GFF3 holds only located features; contacts and whole-protein calls stay in the records.
    """
    records = export_records(_store(db), real_only=real_only)
    if gff3:
        gff3.write_text(to_gff3(records, seqid=gff_seqid))
        typer.echo(f"GFF3 of {len(records)} records written to {gff3}", err=True)
        return
    if parquet:
        try:
            n = to_parquet(records, parquet)
        except ImportError as e:
            raise typer.BadParameter("Parquet export needs pyarrow: pip install 'peptalk-llm[parquet]'") from e
        typer.echo(f"{n} records written to {parquet}", err=True)
        return
    _write(records, Format.jsonl, output)
    typer.echo(f"{len(records)} records", err=True)


@app.command("import")
def import_cmd(
    files: Annotated[list[Path], typer.Argument(help="JSONL exports to add.")],
    db: DbOpt = None,
) -> None:
    """Add exported records to the store, skipping any already present (same call uid)."""
    store = _store(db)
    for f in files:
        added, present = import_jsonl(store, f)
        typer.echo(f"{f}: {added} added, {present} already present", err=True)


@app.command("fasta")
def fasta_cmd(db: DbOpt = None, output: OutOpt = None) -> None:
    """Write each annotated sequence once, named by its MD5, for building a DIAMOND or BLAST database."""
    text = annotated_fasta(_store(db).records("condition = 'real'"))
    if output:
        output.write_text(text)
    else:
        typer.echo(text, nl=False)


@app.command()
def serve(
    db: DbOpt = None,
    host: Annotated[
        str, typer.Option(help="Interface to listen on. The API has no authentication of its own.")
    ] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to listen on.")] = 8000,
    max_sync: Annotated[
        int, typer.Option(help="Most questions POST /annotate answers directly; more need /jobs.")
    ] = 20,
) -> None:
    """Run the REST API (needs the 'server' extra). OpenAPI docs at http://HOST:PORT/docs."""
    try:
        import uvicorn

        from peptalk.server import create_app
    except ImportError as e:
        raise typer.BadParameter("the API needs FastAPI and uvicorn: pip install 'peptalk-llm[server]'") from e
    uvicorn.run(create_app(_store(db), max_sync_questions=max_sync), host=host, port=port)


@app.command()
def tasks(
    show: Annotated[str | None, typer.Option(help="Print the prompt template of this task.")] = None,
    schema: Annotated[str | None, typer.Option(help="Print the JSON Schema of this task's answer.")] = None,
    ask: Annotated[
        bool, typer.Option("--ask", help="Print the ask templates and their claims-file parameters.")
    ] = False,
) -> None:
    """List the tasks (name, prompt version, source, summary), or print one task's prompt or answer schema."""
    if show:
        typer.echo(TEMPLATES[_check_tasks([show])[0]].prompt)
        return
    if schema:
        typer.echo(json.dumps(TEMPLATES[_check_tasks([schema])[0]].json_schema(), indent=2))
        return
    if ask:
        typer.echo(params_table())
        return
    for t in TEMPLATES.values():
        typer.echo(f"{t.name}\t{t.version}\t{t.source}\t{t.summary}\t{','.join(t.params)}")


@app.command()
def headers(fasta: FastaArg, header_profile: ProfileOpt = "auto") -> None:
    """Show the fields parsed from each FASTA header (one JSON object per sequence)."""
    for r in _read_records(fasta, header_profile):
        typer.echo(json.dumps(r.header))


@app.command()
def shuffle(fasta: FastaArg, output: OutOpt = None) -> None:
    """Write a shuffled copy of each sequence (the control the annotator uses), same ids."""
    records = [
        SequenceRecord(id=r.id, description="shuffled", sequence=shuffle_sequence(r.sequence, r.id))
        for r in _read_records(fasta)
    ]
    text = format_fasta(records)
    if output:
        output.write_text(text)
    else:
        typer.echo(text, nl=False)


SchemaPathsArg = Annotated[
    list[Path], typer.Argument(help="Template schema files (schema.yaml) or the folders that hold them.")
]


def _schema_files(paths: list[Path]) -> list[Path]:
    files = [p / "schema.yaml" if p.is_dir() else p for p in paths]
    missing = [str(f) for f in files if not f.exists()]
    if missing:
        raise typer.BadParameter(f"no such schema: {', '.join(missing)}")
    return files


def _codegen():  # type: ignore[no-untyped-def]
    try:
        import linkml  # noqa: F401
    except ImportError as e:
        raise typer.BadParameter("generating schemas needs LinkML: pip install 'peptalk-llm[linkml]'") from e
    from peptalk import codegen

    return codegen


@templates_app.command("generate")
def templates_generate(paths: SchemaPathsArg) -> None:
    """Write schema.py (Pydantic) and <Class>.schema.json next to each template's LinkML schema.yaml."""
    codegen = _codegen()
    for f in _schema_files(paths):
        for written in codegen.write(f):
            typer.echo(f"wrote {written}", err=True)


@templates_app.command("check")
def templates_check(paths: SchemaPathsArg) -> None:
    """Fail if any generated file is missing or differs from what its schema.yaml generates now."""
    codegen = _codegen()
    stale = [p for f in _schema_files(paths) for p in codegen.stale(f)]
    for p in stale:
        typer.echo(f"out of date: {p}", err=True)
    if stale:
        raise typer.Exit(1)
    typer.echo("generated files are current", err=True)


@batch_app.command("submit")
def batch_submit(
    fasta: FastaArg,
    manifest: Annotated[Path, typer.Option("--manifest", help="Where to write the batch manifest (JSON).")],
    task: TaskOpt = None,
    model: ModelOpt = DEFAULT_MODEL,
    effort: EffortOpt = DEFAULT_EFFORT,
    provider: ProviderOpt = None,
    context: ContextOpt = DEFAULT_CONTEXT,
    header_profile: ProfileOpt = "auto",
    param: ParamOpt = None,
    payload: PayloadOpt = None,
    shuffle_control: ShuffleOpt = False,
    structured: StructuredOpt = False,
    db: DbOpt = None,
    reuse: Annotated[bool, typer.Option("--reuse/--no-reuse", help="Leave out questions with a stored answer.")] = True,
    cache_key: KeyOpt = DEFAULT_KEY_TEXT,
    verify_input: VerifyOpt = True,
    max_tokens: MaxTokensOpt = 64_000,
) -> None:
    """Submit every question as one batch to the model's provider."""
    from peptalk import batch

    p = _provider(provider, model, max_tokens=max_tokens)
    questions = build_questions(
        _read_records(fasta, header_profile),
        _check_tasks(task),
        shuffle_control,
        _check_context(context),
        _params(param),
        _payload(payload),
    )
    if reuse:
        store = _store(db, cache_key)
        questions = [q for q in questions if store.lookup(new_annotation(q, p, model, effort, structured)) is None]
    if not questions:
        typer.echo("Every question already has a stored answer; nothing to submit.", err=True)
        raise typer.Exit()
    m = batch.submit(p, questions, model, effort, verify_input=verify_input, structured=structured)
    m.save(manifest)
    typer.echo(
        f"Submitted {m.provider} batch {m.batch_id} with {len(m.entries)} questions; manifest in {manifest}", err=True
    )


@batch_app.command("status")
def batch_status(manifest: Annotated[Path, typer.Argument(help="Manifest written by 'batch submit'.")]) -> None:
    """Show a batch's state and counts."""
    from peptalk.batch import BatchManifest

    m = BatchManifest.load(manifest)
    s = _provider(m.provider, m.model).batch_status(m.batch_id)
    counts = " ".join(f"{k}={v}" for k, v in s.counts.items())
    typer.echo(f"{s.batch_id}\t{s.state}\t{'done' if s.done else 'running'}\t{counts}")


@batch_app.command("collect")
def batch_collect(
    manifest: Annotated[Path, typer.Argument(help="Manifest written by 'batch submit'.")],
    output: OutOpt = None,
    fmt: FormatOpt = Format.jsonl,
    db: DbOpt = None,
    prices: PricesOpt = None,
) -> None:
    """Read a finished batch's results, log them in the store, and write annotation records."""
    from peptalk.batch import BatchManifest, collect

    m = BatchManifest.load(manifest)
    p = _provider(m.provider, m.model)
    s = p.batch_status(m.batch_id)
    if not s.done:
        typer.echo(f"Batch {m.batch_id} is {s.state}; collect it once it has finished.", err=True)
        raise typer.Exit(1)
    annotations = collect(p, m, store=_store(db), prices=load_prices(prices) if prices else None)
    _write(annotations, fmt, output)
    typer.echo(totals_line(annotations), err=True)


if __name__ == "__main__":
    app()
