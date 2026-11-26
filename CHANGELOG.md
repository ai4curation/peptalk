# Changelog

## Unreleased

- **`ask --structured` and `ask --concurrency`:** claims files can use structured output, as `annotate` and
  `batch submit` already could.
- **Null-safe summary lines:** `active-site` (and `combined`) printed `None` for a substitution with no found
  residue or position, and `structure` for a missing fold. OpenAI strict mode sends these as explicit nulls.
- **OpenAI provider run live** with GPT-6.2 Sol and Astra: the input-token check passed on every call, every
  template's strict schema was accepted, `examples/claims.yaml` ran with and without `--structured`, and a
  Batch API job completed.

## 0.2.0

- **Interchange formats defined in LinkML:** `src/peptalk/datamodel/peptalk.yaml` is the single source of truth
  for claims files (`ClaimsFile`) and annotation records (`Annotation`).
  - `just gen-schema` generates the Pydantic models (pydantic-only imports), `claims.schema.json`,
    `annotation.schema.json` and the reference pages in `docs/schema/`.
  - The generated files are committed, and a test fails if they are out of date.
  - LinkML is a development dependency only.
- **Template answers are LinkML too:** each template is `prompt.txt` plus `schema.yaml`.
  - `peptalk templates generate PATH` (and `just gen-schema`) writes the template's Pydantic models and JSON
    Schemas; `peptalk templates check PATH` reports stale files.
  - Shared building blocks are in `templates/common.yaml`, and `pip install 'peptalk-llm[linkml]'` provides the
    generator for plugin authors.
  - Structured-output schemas are cleaned up and adapted per provider (Anthropic transform, OpenAI strict, Gemini).
    A test checks each template against each provider's subset.
- **Claims files in YAML:** claims grouped by protein (`proteins: [{id, claims}]`) or a flat list. Each claim is validated against its
  template, and errors name the claim. TSV and CSV are still accepted for bulk input, chosen by file extension.
- **`expected` and `note`:** optional fields on a claim, never sent to the model and not part of the cache key.
  With `expected`, the totals report how many verdicts agree.
- **New `ask-domain` template:** does the protein contain this Pfam domain, and where?
- **Examples:** `examples/claims.yaml` (and the same claims in `examples/claims.tsv`).
- **Docs:** `docs/claims.md`, with a template table generated from the registry (`peptalk tasks --ask`).

## 0.1.0 (first release)

peptalk (on PyPI as `peptalk-llm`; import and command `peptalk`) asks a frontier LLM what a protein sequence says, from sequence alone, by direct single-shot API calls.

- **Providers:** direct clients for Anthropic (Messages API), Gemini and OpenAI. Each question is one user message
  with no system prompt and no tools. An input-token check confirms that nothing besides the prompt was sent.
- **Tasks:** `features`, `active-site` and `structure`, the prompts of the fable-sequence-to-function study,
  checked byte for byte when blind. Also `function`, `combined`, `localization`, and the ask templates
  `ask-function`, `ask-catalytic-residue` and `ask-localization` (yes/no/uncertain verdicts on one claim, with
  `peptalk ask --claims`).
- **Checks instead of model confidence:**
  - residues at their stated positions, ranges inside the sequence, identifiers well formed;
  - optional shuffled-sequence controls.
- **FASTA headers:** UniProt, NCBI and plain profiles, with all fields kept on each record.
- **Header context:** `--context blind|organism|full`, defaulting to `organism`.
- **Optional payloads:** a stated confidence, a rationale, residue evidence and alternatives (`--with`).
- **Structured output:** provider JSON-Schema output, off unless `--structured` is given.
- **Store:** a SQLite log of every call with full provenance, which also serves as the cache. Cache-key fields
  are configurable; the default covers sequence MD5, task, prompt version, parameters, context, payload, output
  mode, provider, model and effort.
- **Batches:** the batch APIs of Anthropic, OpenAI and Gemini, at half price.
- **Exports:**
  - JSONL export and import that merge without duplicates;
  - Parquet, for querying with DuckDB;
  - GFF3 of located features;
  - FASTA of annotated sequences named by MD5, for DIAMOND or BLAST.
- **REST API:** FastAPI (`peptalk-llm[server]`, `peptalk serve`), with synchronous annotation, background and
  batch jobs, and lookup by sequence MD5.
- **Docs:** `docs/design.md`, `docs/templates.md` and `docs/provider-options.html`.
