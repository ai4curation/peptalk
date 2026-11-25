# peptalk

**peptalk: ask a frontier LLM what a protein sequence says, from sequence alone.**

Despite the name, peptalk works on full-length proteins, not just peptides. It returns Pfam domains with
boundaries, transmembrane helices, signal peptides, catalytic residues that are present or substituted,
secondary structure and contacts, and function.

Each question is one direct API call to Anthropic, Gemini or OpenAI: a single user message holding the prompt
and the sequence, with no system prompt, no tools and no agent. Every call is checked against the sequence,
priced, and logged with full provenance in a local SQLite store, which also serves as the cache. The prompts
come from the [fable-sequence-to-function](https://github.com/ai4curation/fable-sequence-to-function) study
(fs2f).

The package, the import and the command are all `peptalk`.

## Install

```bash
pip install peptalk                 # Claude models
pip install 'peptalk[all]'          # adds Gemini, OpenAI, the REST API and Parquet export
```

With [uv](https://docs.astral.sh/uv/): `uv tool install 'peptalk[all]'`, or try it without
installing: `uvx peptalk --help`.

The extras are `gemini`, `openai`, `server` (REST API) and `parquet`; `all` is all four.

## Set a key

```bash
export ANTHROPIC_API_KEY=sk-ant-...      # Claude
export GEMINI_API_KEY=...                # Gemini (or GOOGLE_API_KEY)
export OPENAI_API_KEY=sk-...             # OpenAI
```

The provider follows from the model name (`claude-*`, `gemini-*`, `gpt-*`), or set `--provider`.

## Quickstart (CLI)

**Annotate a FASTA file.** Each sequence is asked each task. Records go to `results.jsonl`, and progress and a
cost total go to the terminal:

```bash
peptalk annotate proteins.fasta -t features -t active-site -o results.jsonl
peptalk summarize results.jsonl
```

```
id                 task         condition  confidence     protein_name                       call
A0ABQ0J1P6         features     real       checks_passed  ABC transporter ATP-binding prot…  PF00005:27-224
Q2PAY3_asp_to_asn  active-site  real       checks_passed  Rhoptry protein of the ROP2 fam…   active=no lost D436N,R435G,G456T
```

(Answers from live runs: Claude Haiku 5.5 at low effort for the first row, Claude Fable 5.2 at high effort for
the second.)

**One sequence, from standard input, as a table:**

```bash
printf '>my_protein\nMKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQ\n' \
  | peptalk annotate - -t active-site -m claude-opus-5-5 -e medium -f tsv
```

**Add the shuffled control.** The same task is also asked of a shuffled copy of each sequence. An answer is
flagged when the shuffled copy also gets a domain, an "active" call or a recognised name:

```bash
peptalk annotate proteins.fasta -t features --shuffle-control -o results.jsonl
```

**Many sequences: a batch.** A batch costs half as much and returns within 24 hours. Sequences that already
have stored answers are left out:

```bash
peptalk batch submit proteins.fasta -t features --manifest run1.json
peptalk batch status run1.json
peptalk batch collect run1.json -o results.jsonl
```

**Inspect the log and cache.** Every call is logged, and asking again reuses the stored answer:

```bash
peptalk log                                   # the 20 most recent calls
peptalk log --sql "SELECT model, count(*) AS calls, sum(thinking_tokens) AS thinking, round(sum(cost_usd), 2) AS usd
               FROM calls GROUP BY model"
peptalk annotate proteins.fasta --no-reuse    # ask again anyway
```

**Export and share:**

```bash
peptalk export -o mine.jsonl                  # every logged call, one JSON record per line
peptalk import theirs.jsonl                   # merge someone else's export; calls already present are skipped
peptalk export --parquet calls.parquet        # for DuckDB, pandas, polars
peptalk fasta -o annotated.fasta              # each annotated sequence once, named by its MD5, for DIAMOND or BLAST
```

`peptalk --help` lists every command and `peptalk COMMAND --help` its options. `peptalk tasks` lists the tasks with their
prompt versions. `peptalk tasks --show active-site` prints a task's full prompt. `--provider stub` calls no model,
so a pipeline can be checked for free.

## REST API

```bash
pip install 'peptalk[server]'
peptalk serve                                  # http://127.0.0.1:8000, OpenAPI docs at /docs
```

| Endpoint | What it does |
|---|---|
| `POST /annotate` | Annotate a few sequences and wait for the answers (up to `--max-sync` questions, default 20). |
| `POST /jobs` | Start a larger job: `"mode": "live"` asks in the background, `"mode": "batch"` submits one provider batch. Returns a `job_id`. |
| `GET /jobs/{job_id}` | Job status, with the answers once done. Polling a batch job collects it when the provider has finished. |
| `GET /sequences/{seq_md5}` | Every stored answer for a sequence, by the MD5 of its upper-case residues; filter with `?task=` and `?model=`. |
| `GET /health`, `GET /models`, `GET /tasks` | Status and record count; installed providers, defaults and prices; tasks and prompt versions. |

```bash
curl -s localhost:8000/annotate -H 'content-type: application/json' -d '{
  "sequences": [{"id": "my_protein", "sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQ"}],
  "tasks": ["active-site"], "model": "claude-opus-5-5", "effort": "medium"}'

curl -s localhost:8000/jobs -H 'content-type: application/json' \
  -d "{\"fasta\": $(jq -Rs . < proteins.fasta), \"tasks\": [\"features\"], \"mode\": \"batch\"}"
curl -s localhost:8000/jobs/JOB_ID
```

The server takes provider keys from its own environment and logs to the same store as the CLI. It has no
authentication of its own, so it listens on localhost unless you pass `--host`.

## Python

```python
from peptalk import Annotator, Store, read_fasta
from peptalk.providers import provider_for
from peptalk.store import default_db_path

model = "claude-fable-5-2"
annotator = Annotator(provider_for(model), model=model, effort="high", store=Store(default_db_path()))

for a in annotator.annotate(read_fasta("proteins.fasta"), ["active-site"], shuffle_control=True):
    print(a.id, a.condition, a.confidence, (a.answer or {}).get("catalytically_active"), a.cost_usd)
```

Each result is an `Annotation` (a Pydantic model). It carries the parsed `answer`, the reply `text`, the
`checks`, `usage` (input, output and thinking tokens) and `cost_usd`, plus provenance: `seq_md5`,
`prompt_version`, `served_model` and `options`. Batches are in `peptalk.batch`
(`submit`, `collect`) and the API in `peptalk.server.create_app`.

## Tasks

| Task | Prompt | Returns |
|---|---|---|
| `features` (default) | fs2f FEAT | Pfam domains with 1-based boundaries, transmembrane helices, signal peptide, name, EC number, function |
| `active-site` | fs2f PSEUDO | catalytic residues present, canonical residues substituted or missing, active yes/no/uncertain, reason |
| `structure` | fs2f STRFN | helix and strand ranges, fold, 20 long-range contacts, function, functional residues, recognised or not |
| `function` | new, **untested** | summary, family, GO molecular function / process / component terms, EC number |
| `combined` | protein-function-agent reader, **untested merge** | the keys of `features` and `active-site` plus fold, function and recognised, in one question |

Each sequence is sent alone under the header `>sequence`, wrapped at 60 residues. Your FASTA headers are never
sent, so an identifier such as `sp|P00533|EGFR_HUMAN` cannot give the answer away. The three fs2f prompts are
checked byte for byte against the study's scripts in the tests. A task's prompt version is a hash of its text,
so an edited prompt never shares stored answers with the old one.

The default model is `claude-fable-5-2` at `high` effort, the strongest sequence reader in fs2f.
`claude-opus-5-5` costs half as much per token. Effort labels are each provider's own (`low`, `medium`,
`high`, and for Claude also `xhigh` and `max`).

## Checks and confidence

The study found that models state wrong calls as confidently as right ones, so the annotator does not ask the
model how sure it is. Each record instead carries `checks` and a `confidence` derived from them:

- `input_tokens_match`: the call reported exactly as many input tokens as the provider counts for the prompt
  alone, so nothing else was sent. `--no-verify-input` skips the counting request.
- `residues_match_sequence`: each residue the model names is at the position it gives.
- `substitutions_match_sequence`: a residue reported in place of a canonical one is really there.
- `domain_bounds`, `tm_helix_bounds`, `secondary_structure_bounds`, `contacts_valid`: ranges fall inside the
  sequence, and contacts are at least 24 residues apart.
- `pfam_accession_form`, `go_id_form`: identifiers are well formed (not that they exist or are right).
- `shuffled_control` (with `--shuffle-control`): the shuffled copy got no domain, was not called active and was
  not recognised. A transmembrane helix in a shuffled copy is not counted against the answer.

`confidence` is `checks_passed`, `flagged` (a check failed) or `no_answer` (failed call, refusal, tool
invocation in the reply, or no valid answer object). `checks_passed` means only that these checks passed.
Treat every answer as a hypothesis to verify.

## The store: log and cache

Every call that reaches a provider is logged in a SQLite file, failures and refusals included. The file is
`~/.local/share/peptalk/peptalk.db` by default; change it with `--db` or `$PEPTALK_DB`. Each record holds:

- the sequence and its MD5 (the checksum UniParc uses)
- the prompt version and hash
- the provider, the model requested and the model that served the answer
- the effort, the request options as sent, and the client library version
- input, output and thinking tokens, and the prompt-only token count
- cost, stop reason, start and finish times, and the reply text

Before asking, the annotator looks for a usable stored answer whose key fields match. The default key is
`seq_md5,task,prompt_version,provider,model,effort`, so a renamed sequence is still found and an interrupted
run resumes where it stopped. `--cache-key` sets other fields. For example,
`--cache-key seq_md5,task,prompt_version,model` reuses an answer given at any effort, and adding `options`
requires identical request options. Answers are sampled, so reuse returns a stored sample. A reused answer keeps
the `uid` of the call that produced it.

SQLite is the local store because several processes (the CLI, batch collection, the API server) can write to it
at once.

### Querying with DuckDB

DuckDB reads both the live SQLite store and Parquet exports:

```sql
INSTALL sqlite; LOAD sqlite;
ATTACH '~/.local/share/peptalk/peptalk.db' AS peptalk (TYPE sqlite, READ_ONLY);

SELECT model, effort, count(*) AS calls, sum(thinking_tokens) AS thinking, round(sum(cost_usd), 2) AS usd
FROM peptalk.calls GROUP BY ALL;

-- the full record is JSON in the `record` column
SELECT id, json_extract_string(record, '$.answer.catalytically_active') AS active
FROM peptalk.calls WHERE task = 'active-site' AND condition = 'real';

-- a Parquet export (peptalk export --parquet calls.parquet): one row per call, deduplicated by uid
SELECT seq_md5, task, model, protein_name, confidence FROM 'calls.parquet' WHERE condition = 'real';
```

## Sharing results

`peptalk export` writes self-contained JSON records, each with its sequence, `seq_md5` and call `uid`.
`peptalk import` adds only the calls a store does not already have, so exports from several people pool without
duplicates. `peptalk fasta` writes each annotated sequence once, named by its MD5, so DIAMOND or BLAST hits join
back to the records on `seq_md5`. [docs/shared-database.md](https://github.com/ai4curation/peptalk/blob/main/docs/shared-database.md) sketches a shared,
searchable database built from these pieces; it is designed, not built.

## Cost

Anthropic list prices are built in (dollars per million tokens; thinking is billed as output; batches at half
price). For other models pass `--prices prices.json` with `{"model-id": {"input": 1.25, "output": 10.0}}`.
Without a price, cost is left empty.

In a live run, one Fable 5.2 `active-site` question at high effort took 48 seconds and cost $0.19, almost all of
it thinking and output. Twelve Haiku 5.5 questions at low effort cost $0.007 in total. Provider prompt caching
saves nothing here: input is a few percent of the cost, and the fixed prompts (212 to 315 tokens) are below
Anthropic's 512-token caching minimum.

## Refusals

Safety classifiers occasionally decline a protein question. The record then has
`stop_reason: refusal:<category>` and no answer. For Claude models, `--fallback` lets Anthropic's server-side
fallback answer with another model instead. It is off by default because which model answers matters;
`served_model` records it.

## Why direct API calls, and what the study found

fs2f asked most of its Claude questions through the Claude Code command line. That route adds context of its
own and can attach connector tools: a one-sentence prompt carried 5,851 input tokens, and two PSEUDO questions
carried 97,813 and 6,413. Those results should be read as possibly contaminated. A direct API call carries only
what the caller sends, and the `input_tokens_match` check confirms it on every call. In a live test, the
ROP17 active-site question reported 829 input tokens, exactly the prompt's own count.

From the fs2f tests (November 2026; small test sets, sampled answers, mostly through the CLI route above):

- **Domains.** Claude Fable 5.2 named a correct Pfam family for 39 of 45 sampled bacterial and archaeal
  proteins, and Opus 5.5 for 35, with a mean boundary overlap of 0.86. Both almost never gave a domain to a
  shuffled sequence.
- **Obscure families.** Fable 5.2 named the exact family for 8 of 15 obscure domain-of-unknown-function proteins,
  Opus 5.5 for 3 and Gemini 4 Neon for none.
- **Catalytic residues.** Fable 5.2, Opus 5.5 and Gemini 4 Neon called all 20 wild-type kinases active and none
  of the 20 catalytic-Asp mutants. The same substitution at an unannotated position left the call unchanged.
- **Structure and function.** On 12 proteins with no close earlier PDB entry, Fable 5.2 reached 76% three-state
  accuracy (best single-state guess 57%) and 37% long-range contact precision (chance 2%). No model named the
  function correctly for more than half of them.
- **The model matters.** Opus 4.6 invented a domain for 28 of 60 shuffled sequences and missed most active-site
  substitutions.

None of this compares the models with specialised predictors such as InterProScan, DeepTMHMM, SignalP or
AlphaFold. [docs/provider-options.html](https://github.com/ai4curation/peptalk/blob/main/docs/provider-options.html) records how the provider layer was chosen.

## Development

```bash
just test     # pytest and doctests
just check    # ruff, mypy, tests
just build    # sdist and wheel in dist/
just smoke    # live calls with Claude Haiku 5.5 on tests/data/example.fasta (about one cent)
```

The tests call no model. `tests/data` holds one fs2f FEAT protein and the ROP17 kinase with its catalytic
Asp436Asn mutant, with the replies Fable 5.2 gave to them in fs2f.

## Citation

Mungall CJ, Joachimiak MP. General-purpose language models are neurosymbolic reasoners able to annotate
proteins from sequence. Preprint, 2026. https://github.com/ai4curation/fable-sequence-to-function

## License

MIT
