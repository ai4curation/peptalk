# seqfun-annotator

Annotate protein sequences with a general-purpose language model, from the sequence alone: Pfam domains with
boundaries, transmembrane helices, signal peptides, catalytic residues that are present or substituted,
secondary structure and contacts, and function.

This is a packaged version of the prompts and reply-reading rules of
[fable-sequence-to-function](https://github.com/ai4curation/fable-sequence-to-function) (fs2f), which tested
whether frontier models can read protein sequences directly. It calls a model API once per sequence and task:
no agent, no tools, no search. Every answer is recorded with its model, effort, prompt hash, tokens and cost,
and is checked automatically against the sequence.

## What the study found, and what that means here

In the fs2f tests (November 2026; small test sets, sampled answers):

- **Domains.** Claude Fable 5.2 named a correct Pfam family for 39 of 45 sampled bacterial and archaeal
  proteins, Opus 5.5 for 35, with a mean boundary overlap of 0.86. Both almost never gave a domain to a shuffled
  sequence (1 and 0 of 60). All transmembrane helices and signal peptides were recovered, but multi-pass
  helices were sometimes split.
- **Obscure DUFs.** Fable 5.2 named the exact family for 8 of 15 obscure domain-of-unknown-function proteins,
  Opus 5.5 for 3, Gemini 4 Neon for none. Expect misses on obscure families.
- **Catalytic residues.** Fable 5.2, Opus 5.5 and Gemini 4 Neon called all 20 wild-type kinases active and none
  of the 20 catalytic-Asp mutants. Fable 5.2 named the substituted position in 57 of 60 mutants. In a decoy
  control, the same substitution at an unannotated position left the call unchanged (58 of 58 decoys active).
- **Structure.** On 12 proteins with no close earlier PDB entry, Fable 5.2 reached 76% three-state accuracy
  (best single-state guess 57%) and 37% long-range contact precision (chance 2%).
- **Function.** For those 12 proteins no model named the function correctly for more than half.
- **Model matters.** Opus 4.6, an earlier model, invented a domain for 28 of 60 shuffled sequences and missed most
  active-site substitutions. Do not assume an older or smaller model behaves like the frontier ones.
- **No next-residue advantage needed.** Gemini 4 Neon showed no next-residue advantage over shuffled sequence,
  yet detected the catalytic substitutions. The abilities used here do not depend on that test.

Errors come with the same confidence as correct calls. So this tool does not ask the model how sure it is.
It checks each answer instead (see [Checks](#checks-and-confidence)). Treat every answer as a hypothesis for a
curator or a dedicated tool to verify. None of these results compares the models with specialised predictors
(InterProScan, DeepTMHMM, SignalP, AlphaFold).

## Install

```bash
pip install seqfun-annotator               # Anthropic (Claude) models
pip install 'seqfun-annotator[gemini]'     # adds Gemini
pip install 'seqfun-annotator[openai]'     # adds OpenAI
```

or with uv: `uv tool install seqfun-annotator`. Set `ANTHROPIC_API_KEY` (or `GEMINI_API_KEY`,
`OPENAI_API_KEY`).

## Use

```bash
seqfun annotate proteins.fasta -t features -t active-site --shuffle-control -o results.jsonl
seqfun summarize results.jsonl > summary.tsv
```

```
id          task         condition  confidence     protein_name                       call              flags
A0ABQ0J1P6  features     real       checks_passed  ABC transporter ATP-binding prot…  PF00005:27-210
Q2PAY3_mut  active-site  real       checks_passed  Putative serine/threonine kinase   active=no lost D436N
```

The defaults are the best-performing setting in fs2f: `claude-fable-5-2` at `high` effort. `claude-opus-5-5` is
half the price and scored a little lower. For a cheap dry run of a pipeline, use `-m claude-haiku-5-5 -e low`
(untested in fs2f) or `--provider stub`, which calls no model at all.

| Command | What it does |
|---|---|
| `seqfun annotate FASTA` | Ask each task of each sequence; write JSONL (`-f tsv` for the summary table, `-f json`). `-` reads standard input. |
| `seqfun summarize RESULTS.jsonl` | Summary table and totals (answers, cached, errors, flagged, tokens, dollars) of saved results. |
| `seqfun tasks [--show TASK]` | List the tasks, or print a task's full prompt. |
| `seqfun shuffle FASTA` | Write the shuffled control sequences, as the annotator makes them. |
| `seqfun batch submit FASTA --manifest m.json` | Submit everything as one Anthropic message batch (half price; results within 24 hours). |
| `seqfun batch status m.json` / `seqfun batch collect m.json -o results.jsonl` | Poll the batch, then read its results into the same records (and the cache). |

### Tasks

| Task | Prompt | Returns |
|---|---|---|
| `features` | fs2f FEAT, verbatim | Pfam domains with 1-based boundaries, transmembrane helices, signal peptide, name, EC number, one-sentence function |
| `active-site` | fs2f PSEUDO, verbatim | catalytic residues present (role, residue, position), canonical residues substituted or missing, active yes/no/uncertain, reason |
| `structure` | fs2f STRFN, verbatim | helix and strand ranges, fold, 20 long-range contacts, function, functional residues, whether it recognises the protein |
| `function` | new; **not tested in fs2f** | summary, family, GO molecular function / process / component terms, EC number |

Each sequence is sent alone under the header `>sequence`, wrapped at 60 residues, exactly as in fs2f. Your
FASTA headers are never sent, so an identifier such as `sp|P00533|EGFR_HUMAN` cannot give the answer away. The
three fs2f prompts are checked byte for byte against the study in the tests; a changed prompt is a new,
unvalidated task.

### Checks and confidence

Each record has a list of `checks` and a `confidence` derived from them:

- `residues_match_sequence`: every residue the model names (catalytic or functional) is at the position it
  gives. In fs2f, models sometimes moved a catalytic role to a neighbouring residue; this catches misplaced
  positions, not reassigned roles.
- `substitutions_match_sequence`: a residue reported as found in place of a canonical one is really there.
- `domain_bounds`, `tm_helix_bounds`, `secondary_structure_bounds`, `contacts_valid`: ranges fall inside the
  sequence, and contacts are at least 24 residues apart.
- `pfam_accession_form`, `go_id_form`: identifiers are well formed (not that they exist or are right).
- `shuffled_control` (with `--shuffle-control`): the shuffled copy of the sequence got no domain, was not called
  active, and was not recognised as a known protein. A shuffled sequence keeps its composition, so a
  transmembrane helix in it is not counted against the real answer.

`confidence` is `checks_passed`, `flagged` (a check failed) or `no_answer` (failed call, refusal, tool
invocation in the reply, or no valid answer object). `checks_passed` means only that these checks passed.

### Records

One JSON object per line, with `id`, `task`, `condition` (`real` / `shuffled`), the parsed `answer` and the raw
reply `text`, `provider`, `model`, `served_model`, `effort`, `prompt_sha256`, `sequence_sha256`, `usage`
(input, output and thinking tokens), `cost_usd`, `cached`, `batch`, `stop_reason`, `error`, `checks`,
`confidence` and `asked_at`. The answer object is the last JSON object in the reply carrying at least two of
the requested keys, the rule the fs2f scorers used.

### Caching and cost

Answers are cached on disk (`~/.cache/seqfun-annotator`, or `--cache-dir` / `$SEQFUN_CACHE_DIR`), keyed by
provider, model, effort and the full prompt. A rerun asks only what is missing, so an interrupted job resumes
where it stopped. Answers are sampled: a cache hit returns the stored answer, and `--no-cache` asks again.

Costs use Anthropic list prices built into the package (dollars per million tokens; thinking is billed as
output; batches at half price). For other models pass `--prices prices.json` with
`{"model-id": {"input": 1.25, "output": 10.0}}`; without a price, cost is left empty. For scale: the fs2f
rows for Fable 5.2 at high effort record a median of $0.07 per `features` question, $0.16 per `active-site`
question and $0.19 per `structure` question. They were collected through a command-line route that added
context of its own, so direct API calls may cost less; `seqfun summarize` reports what a run actually spent.

### Refusals

Safety classifiers occasionally decline a protein question. The record then has `stop_reason: refusal:<category>`
and no answer. `--fallback` lets Anthropic's server-side fallback answer with another model instead. It is
off by default because which model answers matters, and `served_model` records it when it is on.

### Python

```python
from seqfun_annotator import Annotator, read_fasta
from seqfun_annotator.cache import Cache, default_cache_dir
from seqfun_annotator.providers import get_provider

annotator = Annotator(get_provider("anthropic"), model="claude-fable-5-2", effort="high",
                      cache=Cache(default_cache_dir()))
for a in annotator.annotate(read_fasta("proteins.fasta"), ["active-site"], shuffle_control=True):
    print(a.id, a.condition, a.confidence, (a.answer or {}).get("catalytically_active"))
```

## Development

```bash
just test     # pytest and doctests
just check    # ruff, mypy, tests
just build    # sdist and wheel in dist/ (not published)
just smoke    # live calls with Claude Haiku 5.5 on tests/data/example.fasta (a few cents)
```

Tests call no model. `tests/data` holds one fs2f FEAT protein and the ROP17 kinase with its catalytic
Asp436Asn mutant, with the replies Fable 5.2 gave to them in fs2f.

## Citation

Mungall CJ, Joachimiak MP. General-purpose language models are neurosymbolic reasoners able to annotate
proteins from sequence. Preprint, 2026. https://github.com/ai4curation/fable-sequence-to-function

## License

MIT
