# seqfun-annotator

Annotate protein sequences with a general-purpose language model, from the sequence alone: Pfam domains with
boundaries, transmembrane helices, signal peptides, catalytic residues that are present or substituted,
secondary structure and contacts, and function.

seqfun-annotator is the tooling for the questions of
[fable-sequence-to-function](https://github.com/ai4curation/fable-sequence-to-function) (fs2f), which tested
whether frontier models can read protein sequences directly. It asks each question as one direct API call to
Anthropic, Gemini or OpenAI: one user message holding the prompt and the sequence, with no system prompt, no
tools and no agent. Every call is logged with full provenance, checked against the sequence, and priced.

## Why direct API calls

fs2f asked most of its Claude questions through the Claude Code command line. That route adds context of its
own and can attach connector tools: with the original flags a one-sentence prompt carried 5,851 input tokens,
and two of the PSEUDO questions carried 97,813 and 6,413. Those results should be read as possibly contaminated.
A direct API call carries only what the caller sends, and seqfun checks it: before each call it counts the
prompt's tokens with the provider's counting endpoint, and the record's `input_tokens_match` check fails if the
call reported any more. In a live test of this package, an active-site question on the ROP17 kinase reported 829
input tokens, the count for the prompt alone.

## What fs2f found, and what that means here

From the fs2f tests (November 2026; small test sets, sampled answers, mostly through the CLI route above):

- **Domains.** Claude Fable 5.2 named a correct Pfam family for 39 of 45 sampled bacterial and archaeal
  proteins, Opus 5.5 for 35, with a mean boundary overlap of 0.86. Both almost never gave a domain to a shuffled
  sequence (1 and 0 of 60).
- **Obscure DUFs.** Fable 5.2 named the exact family for 8 of 15 obscure domain-of-unknown-function proteins,
  Opus 5.5 for 3, Gemini 4 Neon for none. Expect misses on obscure families.
- **Catalytic residues.** Fable 5.2, Opus 5.5 and Gemini 4 Neon called all 20 wild-type kinases active and none
  of the 20 catalytic-Asp mutants. The same substitution at an unannotated position left the call unchanged.
- **Structure.** On 12 proteins with no close earlier PDB entry, Fable 5.2 reached 76% three-state accuracy
  (best single-state guess 57%) and 37% long-range contact precision (chance 2%).
- **Function.** For those 12 proteins no model named the function correctly for more than half.
- **Model matters.** Opus 4.6 invented a domain for 28 of 60 shuffled sequences and missed most active-site
  substitutions.
- **No next-residue advantage needed.** Gemini 4 Neon showed no next-residue advantage over shuffled sequence,
  yet detected the catalytic substitutions.

Errors come with the same confidence as correct calls, so seqfun does not ask the model how sure it is. It
checks each answer instead (see [Checks](#checks-and-confidence)). Treat every answer as a hypothesis to verify.
None of these results compares the models with specialised predictors (InterProScan, DeepTMHMM, SignalP,
AlphaFold).

## Install

```bash
pip install seqfun-annotator                     # Anthropic (Claude) models
pip install 'seqfun-annotator[gemini,openai]'    # adds Gemini and OpenAI
```

or `uv tool install 'seqfun-annotator[gemini,openai]'`. Keys come from `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
(or `GOOGLE_API_KEY`) and `OPENAI_API_KEY`.

## Use

```bash
seqfun annotate proteins.fasta -t features -t active-site --shuffle-control -o results.jsonl
seqfun summarize results.jsonl > summary.tsv
```

```
id                 task         condition  confidence     protein_name                       call
A0ABQ0J1P6         features     real       checks_passed  ABC transporter ATP-binding prot…  PF00005:27-224
Q2PAY3_asp_to_asn  active-site  real       checks_passed  Rhoptry protein of the ROP2 fam…   active=no lost D436N,R435G,G456T
```

(Answers from the live tests: Haiku 5.5 at low effort for the first row, Fable 5.2 at high effort for the second.)

The default model is `claude-fable-5-2` at `high` effort, the strongest reader in fs2f. `claude-opus-5-5` is half
the price. The provider follows from the model name (`gemini-*`, `gpt-*`), or set `--provider`. `--provider stub`
calls no model, for checking a pipeline.

| Command | What it does |
|---|---|
| `seqfun annotate FASTA` | Ask each task of each sequence; write JSONL (`-f tsv` for a summary table, `-f json`). `-` reads standard input. |
| `seqfun summarize RESULTS.jsonl` | Summary table and totals (answers, reused, errors, flagged, tokens, dollars). |
| `seqfun log [--sql QUERY]` | List recent calls from the store, or run a read-only SQL query on it. |
| `seqfun export` / `seqfun import FILE...` | Write every logged call as JSONL; add exported calls to a store, skipping ones already present. |
| `seqfun fasta` | Each annotated sequence once, named by its MD5, for `diamond makedb` or `makeblastdb`. |
| `seqfun tasks [--show TASK]` | List the tasks with their prompt versions, or print a task's full prompt. |
| `seqfun shuffle FASTA` | Write the shuffled control sequences, as the annotator makes them. |
| `seqfun batch submit FASTA --manifest m.json` | Submit everything as one batch (Anthropic, Gemini or OpenAI; half price, within 24 hours). |
| `seqfun batch status m.json` / `seqfun batch collect m.json` | Poll the batch, then log its results and write the records. |

### Tasks

| Task | Prompt | Returns |
|---|---|---|
| `features` | fs2f FEAT | Pfam domains with 1-based boundaries, transmembrane helices, signal peptide, name, EC number, function |
| `active-site` | fs2f PSEUDO | catalytic residues present, canonical residues substituted or missing, active yes/no/uncertain, reason |
| `structure` | fs2f STRFN | helix and strand ranges, fold, 20 long-range contacts, function, functional residues, recognised or not |
| `function` | new, **untested** | summary, family, GO molecular function / process / component terms, EC number |
| `combined` | protein-function-agent reader, **untested merge** | the keys of `features` and `active-site` plus fold, function and recognised, in one question |

Each sequence is sent alone under the header `>sequence`, wrapped at 60 residues. Your FASTA headers are never
sent, so an identifier such as `sp|P00533|EGFR_HUMAN` cannot give the answer away. The three fs2f prompts are
checked byte for byte against the study's scripts in the tests. A task's prompt version is a hash of its text,
so an edited prompt is a new version and never shares stored answers with the old one.

### Checks and confidence

Each record has a list of `checks` and a `confidence` derived from them:

- `input_tokens_match`: the call reported exactly as many input tokens as the provider counts for the prompt
  alone. Turn off with `--no-verify-input` (saves one counting request per question).
- `residues_match_sequence`: every residue the model names is at the position it gives.
- `substitutions_match_sequence`: a residue reported as found in place of a canonical one is really there.
- `domain_bounds`, `tm_helix_bounds`, `secondary_structure_bounds`, `contacts_valid`: ranges fall inside the
  sequence; contacts are at least 24 residues apart.
- `pfam_accession_form`, `go_id_form`: identifiers are well formed (not that they exist or are right).
- `shuffled_control` (with `--shuffle-control`): the shuffled copy got no domain, was not called active, and was
  not recognised as a known protein. A transmembrane helix in a shuffled copy is not counted against the answer,
  since a shuffle keeps composition.

`confidence` is `checks_passed`, `flagged` (a check failed) or `no_answer` (failed call, refusal, tool
invocation in the reply, or no valid answer object). `checks_passed` means only that these checks passed.

### The store: log and cache

Every call that reaches a provider is logged in a SQLite file (`~/.local/share/seqfun-annotator/seqfun.db`, or
`--db` / `$SEQFUN_DB`), failures and refusals included. Each record holds the sequence and its MD5, the prompt
version and hash, provider, model, the model that served the answer, effort, the request options as sent, the
client library version, input, output and thinking tokens, the prompt-only token count, cost, stop reason,
start and finish times, and the reply text.

The store is also the cache. Before asking, seqfun looks for a usable stored answer whose key fields match. The
default key is `seq_md5,task,prompt_version,provider,model,effort`, so a renamed sequence is still found and an
interrupted run resumes where it stopped. Set your own with `--cache-key`. For example,
`--cache-key seq_md5,task,prompt_version,model` reuses an answer given at any effort, and adding `options`
requires identical request options. `--no-reuse` asks again. Answers are sampled, so reuse returns a stored
sample. A reused answer keeps the id (`uid`) of the call that produced it.

```bash
seqfun log --sql "SELECT model, count(*), sum(thinking_tokens), round(sum(cost_usd), 2) FROM calls GROUP BY model"
```

### Sharing and merging results

`seqfun export` writes self-contained JSONL records. `seqfun import` adds only the calls a store does not have,
so exports from several people can be pooled without duplicates. `seqfun fasta` writes each annotated sequence
once, named by its MD5, ready for a DIAMOND or BLAST database whose hits join back to the records on `seq_md5`.
[docs/shared-database.md](docs/shared-database.md) sketches a shared, searchable database built on these
pieces. It is designed, not built.

### Batches

`seqfun batch submit` sends every question as one batch to the model's provider: Anthropic Message Batches,
the OpenAI Batch API, or Gemini batch mode. Batches cost half as much and return within 24 hours. Questions with
a stored answer are left out. The manifest file records the batch and each question, so `status` and `collect`
can run later from another shell. Collected results go into the store like live calls, and collecting twice
logs nothing new.

### Cost

Anthropic list prices are built in (dollars per million tokens; thinking is billed as output; batches at half
price). For Gemini and OpenAI models pass `--prices prices.json` with `{"model-id": {"input": 1.25, "output":
10.0}}`; without a price, cost is left empty. In a live test, a Fable 5.2 active-site question at high effort
took 48 seconds and cost $0.19, almost all of it thinking and output. Input was 3.5% of the cost, which is also
why provider-side prompt caching would save nothing here (and the fixed prompts, 212 to 315 tokens, are below
Anthropic's 512-token caching minimum).

### Refusals

Safety classifiers occasionally decline a protein question. The record then has `stop_reason: refusal:<category>`
and no answer. For Anthropic models `--fallback` lets the server-side fallback answer with another model; it is
off by default because which model answers matters, and `served_model` records it when it is on.

### Python

```python
from seqfun_annotator import Annotator, Store, read_fasta
from seqfun_annotator.providers import get_provider
from seqfun_annotator.store import default_db_path

annotator = Annotator(get_provider("anthropic"), model="claude-fable-5-2", effort="high",
                      store=Store(default_db_path()))
for a in annotator.annotate(read_fasta("proteins.fasta"), ["active-site"], shuffle_control=True):
    print(a.id, a.seq_md5, a.condition, a.confidence, (a.answer or {}).get("catalytically_active"))
```

## Development

```bash
just test     # pytest and doctests
just check    # ruff, mypy, tests
just build    # sdist and wheel in dist/ (not published)
just smoke    # live calls with Claude Haiku 5.5 on tests/data/example.fasta (about one cent)
```

Tests call no model. `tests/data` holds one fs2f FEAT protein and the ROP17 kinase with its catalytic Asp436Asn
mutant, with the replies Fable 5.2 gave to them in fs2f. [docs/provider-options.html](docs/provider-options.html)
records how the provider layer was chosen.

## Citation

Mungall CJ, Joachimiak MP. General-purpose language models are neurosymbolic reasoners able to annotate
proteins from sequence. Preprint, 2026. https://github.com/ai4curation/fable-sequence-to-function

## License

MIT
