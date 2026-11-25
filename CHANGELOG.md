# Changelog

## 0.1.0 (first release)

peptalk asks a frontier LLM what a protein sequence says, from sequence alone, by direct single-shot API calls.

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
- **REST API:** FastAPI (`peptalk[server]`, `peptalk serve`), with synchronous annotation, background and
  batch jobs, and lookup by sequence MD5.
- **Docs:** `docs/design.md`, `docs/templates.md` and `docs/provider-options.html`.
