# peptalk design notes

This note covers how peptalk reads FASTA headers, how much of a header the model sees, how answers are modelled
and exported, what a template is, how answer schemas are defined, and the optional answer payloads. The provider
layer is in [provider-options.html](provider-options.html) and the shared database in
[shared-database.md](shared-database.md).

## 1. FASTA header profiles

A header profile turns a header line into open-ended key/value fields (`peptalk.headers`). Every profile sets
`id` (the first word, which is also the record id) and `description` (the rest). The others add what their
format carries:

| Profile | Header shape | Fields added |
|---|---|---|
| `uniprot` | `sp\|P0A7B8\|HSLV_ECOLI ATP-dependent protease subunit HslV OS=Escherichia coli (strain K12) OX=83333 GN=hslV PE=1 SV=2` | `db`, `accession`, `entry_name`, `name`, `organism`, `taxon_id`, `gene`, `protein_existence`, `sequence_version` |
| `ncbi` | `XP_016855012.1 serine/threonine-protein kinase [Homo sapiens]` | `accession`, `name`, `organism` |
| `plain` | anything | none |

`auto` (the default) tries UniProt, then NCBI, then falls back to plain; `--header-profile` picks one.
`peptalk headers FILE` prints what was parsed. The fields are stored on every record (`header`), whatever the
context level, so results can be joined back to accessions and taxa.

## 2. Header context in the prompt

`--context` sets how much of the header the model sees. The level is recorded on every record (`context`) and is
part of the cache key, so blind and informed answers never mix.

| Level | The model sees | Prompt wording |
|---|---|---|
| `blind` | `>sequence` | "using only the sequence" (the fs2f protocol, byte for byte) |
| `organism` (default) | `>sequence OS=Escherichia coli (strain K12) OX=83333` | "using the sequence and the organism given in its header" |
| `full` | the header line as given, accession and name included | "using the sequence and the information in its FASTA header" |

`organism` on a header with no organism gives exactly the blind prompt and is recorded as `blind`.

**Recommendation: `organism` as the default.** The organism is information an annotator legitimately has and a
curator would use: it says whether to expect a signal peptide or a chloroplast transit peptide, which families
are plausible, and how to read an N-terminal hydrophobic stretch. It does not let the model copy an answer. The
`full` header usually carries a database name, and for a UniProt entry the model may recall the entry instead of
reading the sequence. That repeats whatever the name says. fs2f found two submitter names, "Glycerol
dehydrogenase" on a DUF3119 membrane protein and "Methylthioribose kinase" on a DUF7147 protein, that the blind
models did not repeat. A tool meant to check or extend annotation should not be handed the annotation it is
checking. Use `full` when headers carry trusted context that names nothing, such as a sample or a gene-neighbourhood
note. Use `blind` for validation studies and anything compared with fs2f. The shuffled control is asked at the
same level as the real question, so with `full` it says less: a recognised header can carry the answer whatever
the residues.

## 3. Data model and GFF3

Each answer stays open-ended. The record keeps the whole parsed answer object (`answer`), extra keys included,
next to the reply text. Templates add structure where it helps: an answer model for validation, checks, and a
`features` function that lists the answer's located features (`peptalk.schema.Feature`).

`peptalk export --gff3 FILE` writes those features as GFF3. Column 3 is a Sequence Ontology type name and column
2 is `peptalk`. Attributes carry the task, model, context, prompt version, confidence, `seq_md5`, and any
`Dbxref` (for example `Pfam:PF00069`).

| Fits GFF3 (located features) | SO type | Stays in the record |
|---|---|---|
| Pfam domains | `polypeptide_domain` | domain names and accessions, as attributes as well |
| transmembrane helices | `transmembrane_polypeptide_region` | the signal-peptide yes/no of `features` (no coordinates) |
| targeting signals (`localization`) | `signal_peptide`, `transit_peptide`, `nuclear_localization_signal`, else `polypeptide_region` | compartments |
| catalytic residues, present or substituted | `catalytic_residue` (`status=present` or `substituted`) | activity call, enzyme family, EC number |
| helices and strands | `alpha_helix`, `beta_strand` | fold; contacts (residue pairs) |
| functional residues (`structure`) | `polypeptide_region` | function sentences, GO terms, verdicts |

GFF3 describes intervals on one sequence. It has no good place for pairs of residues (contacts), for statements
about the whole protein (function, GO terms, activity, localization, verdicts), or for the reasoning behind a
call. Those stay in the JSON or Parquet record, which a GFF3 feature points back to with its `ID`
(`<uid>.<n>`) and `seq_md5`. Shuffled controls and answers that failed validation are not exported.

## 4. Templates

A template is a prompt, an output schema and defaults. In peptalk it is a directory under
`src/peptalk/templates/` holding:

- `prompt.txt`: the prompt, with placeholders.
  - `{{basis}}` or `{{Basis}}` is the context wording: "using only the sequence" when blind.
  - `{{payload}}` is where requested payload keys are asked for.
  - `{{header}}` is the header line the model sees.
  - `{{sequence}}` is the residues, 60 per line.
  - Ask templates add their own placeholders, such as `{{term}}` or `{{position}}`.
- `__init__.py`: `TEMPLATE = Template(...)` with the answer model, optional `checks`, `control_signal`,
  `features` and `headline` functions, `params` for its own placeholders, and defaults (`default_effort`,
  `recommended_model`).

Built-in templates register themselves. Another package can add templates through the `peptalk.templates` entry
point group, or with `peptalk.templates.register()`. A template's version is the first 12 hex digits of the
SHA-256 of its prompt file, so any edit gives a new version. The cache key includes the version, so answers to
an old prompt are never reused for a new one. [templates.md](templates.md) walks through adding one (the shipped
`localization` template).

### Ask templates

Ask templates put one claim to the model and take a verdict (`yes`, `no` or `uncertain`) plus a reason. Each
claim is named by parameters:

| Template | Parameters | Question |
|---|---|---|
| `ask-function` | `term`, `label` | does the protein have the function of this GO term? |
| `ask-catalytic-residue` | `position`, `residue` | is this residue catalytic? (also checks the claimed residue is at the position) |
| `ask-localization` | `compartment` | is the protein located there? |
| `ask-domain` | `accession`, `name` | does the protein contain this Pfam domain, and where? |

`peptalk ask FASTA --claims claims.yaml` takes one question per claim (see [claims.md](claims.md)), so existing annotations (from GO, UniProt or
ai-gene-review) can be checked one at a time and evaluation sets built from them. Context levels, payloads and
shuffled controls work as for the other templates; a "yes" for a shuffled copy is flagged. The parameters are
part of the cache key.

## 5. Schemas: LinkML for everything shared, generated Pydantic at runtime

The protocol does not change: the prompt asks for JSON in plain text, peptalk takes the last JSON object in the
reply that carries the requested keys, and validates it against the template's answer model. Structured output
(constrained decoding) is opt-in with `--structured`. The template's JSON Schema then goes to the provider:
`output_config.format` for Anthropic, `text.format` for OpenAI, `response_json_schema` for Gemini.

It stays opt-in because it changes the question:

- **It adds hidden context.** On Claude Haiku 5.5 a `features` prompt of 400 tokens became a request of 2,447
  input tokens with the schema, which the provider adds itself. The input-token check counts the request with the
  schema, so it still passes.
- **It can change the answer.** In one sample of each, Haiku named E. coli HslV correctly in text mode and as a
  ClpP-family protease with structured output.
- **It differs between providers** in which JSON Schema features they accept and how they enforce them.

**The rule: LinkML is the single source of truth for interchange schemas.** These are the files people and
programs exchange:

- **claims files** (class `ClaimsFile`);
- **annotation records**, the rows of the store, of JSONL and Parquet exports and of a future shared database
  (class `Annotation`, with `Usage` and `Check`).

Both are defined in [`src/peptalk/datamodel/peptalk.yaml`](../src/peptalk/datamodel/peptalk.yaml), and
`just gen-schema` generates from it:

- `src/peptalk/datamodel/peptalk.py`, Pydantic models that import only pydantic and the standard library;
- `claims.schema.json` and `annotation.schema.json`;
- reference pages in [docs/schema/](schema/index.md).

The generated files are committed, and `tests/test_datamodel.py` (run in CI) fails if regenerating them gives
any difference. LinkML is a development dependency only: nothing at runtime imports linkml or linkml-runtime.
The runtime code subclasses the generated interchange models only to give empty defaults and to add checks the
schema cannot express, such as a claim's parameters matching its template; a test checks that the subclasses add
no fields.

**Template answer schemas are LinkML too.** A template is a prompt plus a schema: `prompt.txt` next to a
LinkML `schema.yaml`. `peptalk templates generate` (and `just gen-schema` for the built-in templates) writes
that template's Pydantic models (`schema.py`, pydantic-only imports) and the JSON Schema of each answer class.
The shared building blocks (payload keys, domains, residues, GO terms, `[start, end]` ranges) are in
`src/peptalk/templates/common.yaml`. Plugins follow the same steps ([templates.md](templates.md)).

Before an answer schema is sent as structured output it is cleaned up deterministically and adapted per provider
(`peptalk.structured`): Anthropic's SDK transform, OpenAI's strict form, Gemini as is. A test checks every
template's schema against each provider's documented subset. JSON Schemas are generated without explicit nulls,
so an optional field is simply not required; the OpenAI strict form adds the nulls back, because strict mode
requires every property.

`peptalk tasks --schema NAME` and `GET /tasks/{name}/schema` print a template's JSON Schema.

## 6. Optional payloads

`--with confidence,rationale,evidence,alternatives` asks for extra keys alongside the annotation:

| Payload | How it is asked |
|---|---|
| `confidence` | "a number from 0 to 1, your probability that your main answer is correct": a stated probability, not a token log-probability, and uncalibrated until compared with a reference set |
| `rationale` | two or three sentences on the features of the sequence that led to the answer |
| `evidence` | the residues the answer rests on (position, residue, note); peptalk checks each cited residue against the sequence |
| `alternatives` | answers considered and rejected, and why |

They cost tokens. Asking for them can also change the answer itself: a model asked for a rationale or for
alternatives may reason differently. The chosen payload is therefore recorded on every record and is part of the
cache key, and an evaluation run should fix one payload choice for all its questions. With no payload and `--context blind`, the
fs2f prompts are sent unchanged.

The record-level `confidence` (`checks_passed`, `flagged`, `no_answer`) is peptalk's own result from its checks.
It is unrelated to the model's stated `confidence` in `answer`.
