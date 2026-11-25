"""The ``seqfun`` command line."""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from seqfun_annotator import __version__
from seqfun_annotator.annotator import Annotator, build_questions
from seqfun_annotator.cache import Cache, default_cache_dir
from seqfun_annotator.fasta import SequenceRecord, format_fasta, parse_fasta, shuffle_sequence
from seqfun_annotator.pricing import load_prices
from seqfun_annotator.providers import PROVIDERS, get_provider, provider_for_model
from seqfun_annotator.report import dumps_json, read_jsonl, totals_line, write_jsonl, write_tsv
from seqfun_annotator.schema import Annotation
from seqfun_annotator.tasks import TASKS

app = typer.Typer(
    help="Annotate protein sequences with a frontier language model, from sequence alone.", no_args_is_help=True
)
batch_app = typer.Typer(help="Anthropic Message Batches: half price, results within 24 hours.", no_args_is_help=True)
app.add_typer(batch_app, name="batch")

DEFAULT_MODEL = "claude-fable-5-2"
DEFAULT_EFFORT = "high"


class Format(str, Enum):
    jsonl = "jsonl"
    json = "json"
    tsv = "tsv"


FastaArg = Annotated[Path, typer.Argument(help="FASTA file, or - for standard input.", allow_dash=True)]
TaskOpt = Annotated[
    list[str], typer.Option("--task", "-t", help=f"Task to run; repeatable. One of: {', '.join(TASKS)}.")
]
ModelOpt = Annotated[str, typer.Option("--model", "-m", help="Model id.")]
EffortOpt = Annotated[str, typer.Option("--effort", "-e", help="Effort / thinking level (provider's own labels).")]
ShuffleOpt = Annotated[
    bool, typer.Option("--shuffle-control/--no-shuffle-control", help="Also ask each task of a shuffled copy.")
]
CacheDirOpt = Annotated[Path | None, typer.Option(help="Cache directory [default: ~/.cache/seqfun-annotator].")]
PricesOpt = Annotated[Path | None, typer.Option(help="JSON file of extra prices per model ($ per million tokens).")]
OutOpt = Annotated[Path | None, typer.Option("--output", "-o", help="Write here instead of standard output.")]
FormatOpt = Annotated[
    Format, typer.Option("--format", "-f", help="jsonl: one full record per line; tsv: a summary table.")
]


def _read_records(fasta: Path) -> list[SequenceRecord]:
    text = sys.stdin.read() if str(fasta) == "-" else fasta.read_text()
    return parse_fasta(text)


def _check_tasks(tasks: list[str] | None) -> list[str]:
    tasks = tasks or ["features"]
    bad = [t for t in tasks if t not in TASKS]
    if bad:
        raise typer.BadParameter(f"unknown task(s) {', '.join(bad)}; choose from {', '.join(TASKS)}")
    return tasks


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
    provider: Annotated[
        str | None, typer.Option(help=f"One of {', '.join(PROVIDERS)} [default: from the model name].")
    ] = None,
    shuffle_control: ShuffleOpt = False,
    output: OutOpt = None,
    fmt: FormatOpt = Format.jsonl,
    cache: Annotated[bool, typer.Option("--cache/--no-cache", help="Reuse and store answers in the cache.")] = True,
    cache_dir: CacheDirOpt = None,
    prices: PricesOpt = None,
    concurrency: Annotated[int, typer.Option(help="Questions asked at once.")] = 4,
    fallback: Annotated[
        bool, typer.Option(help="Anthropic only: let another model answer a declined request.")
    ] = False,
    max_tokens: Annotated[
        int, typer.Option(help="Anthropic only: output limit per answer, thinking included.")
    ] = 64_000,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="No progress or totals on standard error.")] = False,
) -> None:
    """Annotate every sequence in a FASTA file. Each sequence is sent alone, headed '>sequence'."""
    records = _read_records(fasta)
    tasks = _check_tasks(task)
    name = provider or provider_for_model(model)
    options = {"fallback": fallback, "max_tokens": max_tokens} if name == "anthropic" else {}
    annotator = Annotator(
        get_provider(name, **options),
        model=model,
        effort=effort,
        cache=Cache(cache_dir or default_cache_dir()) if cache else None,
        prices=load_prices(prices) if prices else None,
        concurrency=concurrency,
    )

    def progress(a: Annotation) -> None:
        if not quiet:
            how = "cached" if a.cached else (a.error or a.confidence)
            typer.echo(f"{a.id}\t{a.task}\t{a.condition}\t{how}", err=True)

    annotations = annotator.annotate(records, tasks, shuffle_control=shuffle_control, progress=progress)
    _write(annotations, fmt, output)
    if not quiet:
        typer.echo(totals_line(annotations), err=True)


@app.command()
def summarize(
    results: Annotated[Path, typer.Argument(help="JSONL file written by 'seqfun annotate' or 'seqfun batch collect'.")],
    output: OutOpt = None,
) -> None:
    """Print a summary table (TSV) of saved results, and their totals on standard error."""
    annotations = read_jsonl(results)
    _write(annotations, Format.tsv, output)
    typer.echo(totals_line(annotations), err=True)


@app.command()
def tasks(
    show: Annotated[str | None, typer.Option(help="Print the full prompt of this task.")] = None,
) -> None:
    """List the tasks, or print one task's prompt."""
    if show:
        typer.echo(TASKS[_check_tasks([show])[0]].prompt_for("<sequence>"))
        return
    for t in TASKS.values():
        typer.echo(f"{t.name}\t{t.source}\t{t.summary}")


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


@batch_app.command("submit")
def batch_submit(
    fasta: FastaArg,
    manifest: Annotated[Path, typer.Option("--manifest", help="Where to write the batch manifest (JSON).")],
    task: TaskOpt = None,
    model: ModelOpt = DEFAULT_MODEL,
    effort: EffortOpt = DEFAULT_EFFORT,
    shuffle_control: ShuffleOpt = False,
    cache: Annotated[bool, typer.Option("--cache/--no-cache", help="Leave out questions already in the cache.")] = True,
    cache_dir: CacheDirOpt = None,
    max_tokens: Annotated[int, typer.Option(help="Output limit per answer, thinking included.")] = 64_000,
) -> None:
    """Submit every question as one Anthropic message batch."""
    from seqfun_annotator.batch import build_manifest, submit

    questions = build_questions(_read_records(fasta), _check_tasks(task), shuffle_control)
    if cache:
        store = Cache(cache_dir or default_cache_dir())
        questions = [q for q in questions if store.get("anthropic", model, effort, q.prompt) is None]
    if not questions:
        typer.echo("Every question is already in the cache; nothing to submit.", err=True)
        raise typer.Exit()
    m = submit(build_manifest(questions, model, effort, max_tokens))
    m.save(manifest)
    typer.echo(f"Submitted batch {m.batch_id} with {len(m.entries)} questions; manifest in {manifest}", err=True)


@batch_app.command("status")
def batch_status(manifest: Annotated[Path, typer.Argument(help="Manifest written by 'batch submit'.")]) -> None:
    """Show a batch's processing status and counts."""
    from seqfun_annotator.batch import BatchManifest, status

    b = status(BatchManifest.load(manifest))
    c = b.request_counts
    typer.echo(f"{b.id}\t{b.processing_status}\tprocessing={c.processing} succeeded={c.succeeded} errored={c.errored}")


@batch_app.command("collect")
def batch_collect(
    manifest: Annotated[Path, typer.Argument(help="Manifest written by 'batch submit'.")],
    output: OutOpt = None,
    fmt: FormatOpt = Format.jsonl,
    cache_dir: CacheDirOpt = None,
    prices: PricesOpt = None,
) -> None:
    """Read an ended batch's results, store them in the cache, and write annotation records."""
    from seqfun_annotator.batch import BatchManifest, collect, status

    m = BatchManifest.load(manifest)
    b = status(m)
    if b.processing_status != "ended":
        typer.echo(f"Batch {m.batch_id} is {b.processing_status}; collect it once it has ended.", err=True)
        raise typer.Exit(1)
    annotations = collect(
        m, cache=Cache(cache_dir or default_cache_dir()), prices=load_prices(prices) if prices else None
    )
    _write(annotations, fmt, output)
    typer.echo(totals_line(annotations), err=True)


if __name__ == "__main__":
    app()
