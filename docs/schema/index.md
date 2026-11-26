# peptalk interchange formats

The files peptalk reads and writes for exchange: claims files (claims about proteins, one question each) and annotation records (one model call with its answer, provenance, checks and cost; the rows of the SQLite store, of JSONL and Parquet exports, and of a future shared database). This schema is the single source of truth: peptalk/datamodel/peptalk.py (Pydantic) and the JSON Schemas next to it are generated from it with `just gen-schema`. Answer shapes of individual tasks are defined by their templates, not here.

URI: https://w3id.org/ai4curation/peptalk

Name: peptalk



## Classes

| Class | Description |
| --- | --- |
| [Annotation](Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |
| [Any](Any.md) | Any value (an open-ended object) |
| [Check](Check.md) | One automatic check of an answer against the sequence, the claim or the shuff... |
| [ClaimBody](ClaimBody.md) | One claim, without the protein it is about (as written under a protein) |
| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[Claim](Claim.md) | One claim about one protein |
| [ClaimsFile](ClaimsFile.md) | A claims file |
| [ProteinClaims](ProteinClaims.md) | The claims about one protein |
| [Usage](Usage.md) | Token counts for one call |



## Slots

| Slot | Description |
| --- | --- |
| [annotator_version](annotator_version.md) | The peptalk version that made the call |
| [answer](answer.md) | The answer object parsed from the reply: open-ended, shaped by the template (... |
| [batch](batch.md) | True if asked through a provider batch API |
| [batch_id](batch_id.md) | The provider's batch id |
| [cache_creation_input_tokens](cache_creation_input_tokens.md) |  |
| [cache_read_input_tokens](cache_read_input_tokens.md) |  |
| [cached](cached.md) | True if this answer was reused from the store instead of asked again |
| [checks](checks.md) | The automatic checks of the answer |
| [claims](claims.md) | Claims listed one by one, each naming its protein |
| [client](client.md) | The client library and its version |
| [condition](condition.md) | The real sequence, or its shuffled copy (the control) |
| [confidence](confidence.md) | peptalk's own result from its checks (not the model's stated confidence, whic... |
| [context](context.md) | How much of the FASTA header the model saw |
| [cost_usd](cost_usd.md) | Cost in US dollars at list price, if the model has a price |
| [description](description.md) | The rest of the FASTA header line |
| [detail](detail.md) | What failed, if anything |
| [duration_ms](duration_ms.md) |  |
| [effort](effort.md) | The effort or thinking level, in the provider's own labels |
| [error](error.md) | Why the call failed, if it did |
| [expected](expected.md) | The verdict you expect, for benchmarks |
| [expected_input_tokens](expected_input_tokens.md) | The provider's count of the request alone; checked against the reported input |
| [fallback_used](fallback_used.md) | True if a server-side fallback model answered instead of the one requested |
| [finished_at](finished_at.md) | When the call finished (ISO 8601, UTC) |
| [header](header.md) | Every field parsed from the FASTA header (accession, organism, taxon id,  |
| [id](id.md) | The protein, as the first word of its FASTA header |
| [input_tokens](input_tokens.md) |  |
| [model](model.md) | The model requested |
| [name](name.md) |  |
| [note](note.md) | Any text |
| [options](options.md) | Every request field besides the prompt, as sent |
| [output](output.md) | Free text parsed for JSON (the default), or provider structured output |
| [output_tokens](output_tokens.md) |  |
| [params](params.md) | The template's parameters, all of them and no others, such as {position: 436,... |
| [passed](passed.md) |  |
| [payload](payload.md) | Optional answer keys asked for (confidence, rationale, evidence, alternatives... |
| [prompt_sha256](prompt_sha256.md) | SHA-256 of the full prompt sent |
| [prompt_version](prompt_version.md) | First 12 hex digits of the SHA-256 of the template's prompt file |
| [proteins](proteins.md) | Claims grouped by protein |
| [provider](provider.md) | anthropic, gemini, openai, or stub |
| [response_id](response_id.md) | The provider's id for the response |
| [seq_md5](seq_md5.md) | MD5 of the upper-case residues asked, the checksum UniParc uses |
| [sequence](sequence.md) | The residues asked (for a shuffled control, the shuffled residues) |
| [sequence_length](sequence_length.md) |  |
| [served_model](served_model.md) | The model that answered, as the provider reports it |
| [started_at](started_at.md) | When the call started (ISO 8601, UTC) |
| [stop_reason](stop_reason.md) | Why the model stopped, as the provider reports it; `refusal:<category>` for a... |
| [task](task.md) | The ask template that puts the claim to the model, such as ask-catalytic-resi... |
| [text](text.md) | The model's reply, verbatim |
| [thinking_tokens](thinking_tokens.md) |  |
| [uid](uid.md) | The call that produced the answer |
| [usage](usage.md) | Token counts |
| [validation_error](validation_error.md) | Why the answer object failed the template's answer model, if it did |


## Enumerations

| Enumeration | Description |
| --- | --- |
| [Condition](Condition.md) |  |
| [Confidence](Confidence.md) |  |
| [HeaderContext](HeaderContext.md) |  |
| [OutputMode](OutputMode.md) |  |
| [Verdict](Verdict.md) |  |


## Types

| Type | Description |
| --- | --- |
| [Boolean](Boolean.md) | A binary (true or false) value |
| [Curie](Curie.md) | a compact URI |
| [Date](Date.md) | a date (year, month and day) in an idealized calendar |
| [DateOrDatetime](DateOrDatetime.md) | Either a date or a datetime |
| [Datetime](Datetime.md) | The combination of a date and time |
| [Decimal](Decimal.md) | A real number with arbitrary precision that conforms to the xsd:decimal speci... |
| [Double](Double.md) | A real number that conforms to the xsd:double specification |
| [Float](Float.md) | A real number that conforms to the xsd:float specification |
| [Integer](Integer.md) | An integer |
| [Jsonpath](Jsonpath.md) | A string encoding a JSON Path |
| [Jsonpointer](Jsonpointer.md) | A string encoding a JSON Pointer |
| [Ncname](Ncname.md) | Prefix part of CURIE |
| [Nodeidentifier](Nodeidentifier.md) | A URI, CURIE or BNODE that represents a node in a model |
| [Objectidentifier](Objectidentifier.md) | A URI or CURIE that represents an object in the model |
| [Sparqlpath](Sparqlpath.md) | A string encoding a SPARQL Property Path |
| [String](String.md) | A character string |
| [Time](Time.md) | A time object represents a (local) time of day, independent of any particular... |
| [Uri](Uri.md) | a complete URI |
| [Uriorcurie](Uriorcurie.md) | a URI or a CURIE |


## Subsets

| Subset | Description |
| --- | --- |
