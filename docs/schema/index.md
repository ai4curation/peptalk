# peptalk interchange formats

The files peptalk reads and writes for exchange: claims files (claims about proteins, one question each) and annotation records (one model call with its answer, provenance, checks and cost; the rows of the SQLite store, of JSONL and Parquet exports, and of a future shared database). This schema is the single source of truth: peptalk/datamodel/peptalk.py (Pydantic) and the JSON Schemas next to it are generated from it with `just gen-schema`. Answer shapes of individual tasks are defined by their templates, not here.

URI: https://w3id.org/ai4curation/peptalk

Name: peptalk



## Classes

| Class | Description |
| --- | --- |
| [Annotation](classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |
| [Any](classes/Any.md) | Any value (an open-ended object) |
| [Check](classes/Check.md) | One automatic check of an answer against the sequence, the claim or the shuff... |
| [ClaimBody](classes/ClaimBody.md) | One claim, without the protein it is about (as written under a protein) |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Claim](classes/Claim.md) | One claim about one protein |
| [ClaimsFile](classes/ClaimsFile.md) | A claims file |
| [ProteinClaims](classes/ProteinClaims.md) | The claims about one protein |
| [Usage](classes/Usage.md) | Token counts for one call |



## Slots

| Slot | Description |
| --- | --- |
| [annotator_version](slots/annotator_version.md) | The peptalk version that made the call |
| [answer](slots/answer.md) | The answer object parsed from the reply: open-ended, shaped by the template (... |
| [batch](slots/batch.md) | True if asked through a provider batch API |
| [batch_id](slots/batch_id.md) | The provider's batch id |
| [cache_creation_input_tokens](slots/cache_creation_input_tokens.md) |  |
| [cache_read_input_tokens](slots/cache_read_input_tokens.md) |  |
| [cached](slots/cached.md) | True if this answer was reused from the store instead of asked again |
| [checks](slots/checks.md) | The automatic checks of the answer |
| [claims](slots/claims.md) | Claims listed one by one, each naming its protein |
| [client](slots/client.md) | The client library and its version |
| [condition](slots/condition.md) | The real sequence, or its shuffled copy (the control) |
| [confidence](slots/confidence.md) | peptalk's own result from its checks (not the model's stated confidence, whic... |
| [context](slots/context.md) | How much of the FASTA header the model saw |
| [cost_usd](slots/cost_usd.md) | Cost in US dollars at list price, if the model has a price |
| [description](slots/description.md) | The rest of the FASTA header line |
| [detail](slots/detail.md) | What failed, if anything |
| [duration_ms](slots/duration_ms.md) |  |
| [effort](slots/effort.md) | The effort or thinking level, in the provider's own labels |
| [error](slots/error.md) | Why the call failed, if it did |
| [expected](slots/expected.md) | The verdict you expect, for benchmarks |
| [expected_input_tokens](slots/expected_input_tokens.md) | The provider's count of the request alone; checked against the reported input |
| [fallback_used](slots/fallback_used.md) | True if a server-side fallback model answered instead of the one requested |
| [finished_at](slots/finished_at.md) | When the call finished (ISO 8601, UTC) |
| [header](slots/header.md) | Every field parsed from the FASTA header (accession, organism, taxon id,  |
| [id](slots/id.md) | The protein, as the first word of its FASTA header |
| [input_tokens](slots/input_tokens.md) |  |
| [model](slots/model.md) | The model requested |
| [name](slots/name.md) |  |
| [note](slots/note.md) | Any text |
| [options](slots/options.md) | Every request field besides the prompt, as sent |
| [output](slots/output.md) | Free text parsed for JSON (the default), or provider structured output |
| [output_tokens](slots/output_tokens.md) |  |
| [params](slots/params.md) | The template's parameters, all of them and no others, such as {position: 436,... |
| [passed](slots/passed.md) |  |
| [payload](slots/payload.md) | Optional answer keys asked for (confidence, rationale, evidence, alternatives... |
| [prompt_sha256](slots/prompt_sha256.md) | SHA-256 of the full prompt sent |
| [prompt_version](slots/prompt_version.md) | First 12 hex digits of the SHA-256 of the template's prompt file |
| [proteins](slots/proteins.md) | Claims grouped by protein |
| [provider](slots/provider.md) | anthropic, gemini, openai, or stub |
| [response_id](slots/response_id.md) | The provider's id for the response |
| [seq_md5](slots/seq_md5.md) | MD5 of the upper-case residues asked, the checksum UniParc uses |
| [sequence](slots/sequence.md) | The residues asked (for a shuffled control, the shuffled residues) |
| [sequence_length](slots/sequence_length.md) |  |
| [served_model](slots/served_model.md) | The model that answered, as the provider reports it |
| [started_at](slots/started_at.md) | When the call started (ISO 8601, UTC) |
| [stop_reason](slots/stop_reason.md) | Why the model stopped, as the provider reports it; `refusal:<category>` for a... |
| [task](slots/task.md) | The ask template that puts the claim to the model, such as ask-catalytic-resi... |
| [text](slots/text.md) | The model's reply, verbatim |
| [thinking_tokens](slots/thinking_tokens.md) |  |
| [uid](slots/uid.md) | The call that produced the answer |
| [usage](slots/usage.md) | Token counts |
| [validation_error](slots/validation_error.md) | Why the answer object failed the template's answer model, if it did |


## Enumerations

| Enumeration | Description |
| --- | --- |
| [Condition](enums/Condition.md) |  |
| [Confidence](enums/Confidence.md) |  |
| [HeaderContext](enums/HeaderContext.md) |  |
| [OutputMode](enums/OutputMode.md) |  |
| [Verdict](enums/Verdict.md) |  |


## Types

| Type | Description |
| --- | --- |
| [Boolean](types/Boolean.md) | A binary (true or false) value |
| [Curie](types/Curie.md) | a compact URI |
| [Date](types/Date.md) | a date (year, month and day) in an idealized calendar |
| [DateOrDatetime](types/DateOrDatetime.md) | Either a date or a datetime |
| [Datetime](types/Datetime.md) | The combination of a date and time |
| [Decimal](types/Decimal.md) | A real number with arbitrary precision that conforms to the xsd:decimal speci... |
| [Double](types/Double.md) | A real number that conforms to the xsd:double specification |
| [Float](types/Float.md) | A real number that conforms to the xsd:float specification |
| [Integer](types/Integer.md) | An integer |
| [Jsonpath](types/Jsonpath.md) | A string encoding a JSON Path |
| [Jsonpointer](types/Jsonpointer.md) | A string encoding a JSON Pointer |
| [Ncname](types/Ncname.md) | Prefix part of CURIE |
| [Nodeidentifier](types/Nodeidentifier.md) | A URI, CURIE or BNODE that represents a node in a model |
| [Objectidentifier](types/Objectidentifier.md) | A URI or CURIE that represents an object in the model |
| [Sparqlpath](types/Sparqlpath.md) | A string encoding a SPARQL Property Path |
| [String](types/String.md) | A character string |
| [Time](types/Time.md) | A time object represents a (local) time of day, independent of any particular... |
| [Uri](types/Uri.md) | a complete URI |
| [Uriorcurie](types/Uriorcurie.md) | a URI or a CURIE |


## Subsets

| Subset | Description |
| --- | --- |
