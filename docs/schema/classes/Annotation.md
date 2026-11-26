---
search:
  boost: 10.0
---

# Class: Annotation 


_One answer to one task for one sequence, with provenance, checks and cost. A reused (cached) answer keeps the uid of the call that produced it, so merged exports deduplicate on uid._



<div data-search-exclude markdown="1">



URI: [peptalk:class/Annotation](https://w3id.org/ai4curation/peptalk/class/Annotation)





```mermaid
 classDiagram
    class Annotation
    click Annotation href "../../classes/Annotation/"
      Annotation : annotator_version
        
      Annotation : answer
        
          
    
        
        
        Annotation --> "0..1" Any : answer
        click Any href "../../classes/Any/"
    

        
      Annotation : batch
        
      Annotation : batch_id
        
      Annotation : cached
        
      Annotation : checks
        
          
    
        
        
        Annotation --> "*" Check : checks
        click Check href "../../classes/Check/"
    

        
      Annotation : client
        
      Annotation : condition
        
          
    
        
        
        Annotation --> "1" Condition : condition
        click Condition href "../../enums/Condition/"
    

        
      Annotation : confidence
        
          
    
        
        
        Annotation --> "1" Confidence : confidence
        click Confidence href "../../enums/Confidence/"
    

        
      Annotation : context
        
          
    
        
        
        Annotation --> "1" HeaderContext : context
        click HeaderContext href "../../enums/HeaderContext/"
    

        
      Annotation : cost_usd
        
      Annotation : description
        
      Annotation : duration_ms
        
      Annotation : effort
        
      Annotation : error
        
      Annotation : expected
        
          
    
        
        
        Annotation --> "0..1" Verdict : expected
        click Verdict href "../../enums/Verdict/"
    

        
      Annotation : expected_input_tokens
        
      Annotation : fallback_used
        
      Annotation : finished_at
        
      Annotation : header
        
          
    
        
        
        Annotation --> "0..1" Any : header
        click Any href "../../classes/Any/"
    

        
      Annotation : id
        
      Annotation : model
        
      Annotation : note
        
      Annotation : options
        
          
    
        
        
        Annotation --> "0..1" Any : options
        click Any href "../../classes/Any/"
    

        
      Annotation : output
        
          
    
        
        
        Annotation --> "1" OutputMode : output
        click OutputMode href "../../enums/OutputMode/"
    

        
      Annotation : params
        
          
    
        
        
        Annotation --> "0..1" Any : params
        click Any href "../../classes/Any/"
    

        
      Annotation : payload
        
      Annotation : prompt_sha256
        
      Annotation : prompt_version
        
      Annotation : provider
        
      Annotation : response_id
        
      Annotation : seq_md5
        
      Annotation : sequence
        
      Annotation : sequence_length
        
      Annotation : served_model
        
      Annotation : started_at
        
      Annotation : stop_reason
        
      Annotation : task
        
      Annotation : text
        
      Annotation : uid
        
      Annotation : usage
        
          
    
        
        
        Annotation --> "0..1" Usage : usage
        click Usage href "../../classes/Usage/"
    

        
      Annotation : validation_error
        
      
```




<!-- no inheritance hierarchy -->

## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [uid](../slots/uid.md) | 1 <br/> [String](../types/String.md) | The call that produced the answer | direct |
| [id](../slots/id.md) | 1 <br/> [String](../types/String.md) | The first word of the sequence's FASTA header, as given | direct |
| [description](../slots/description.md) | 0..1 <br/> [String](../types/String.md) | The rest of the FASTA header line | direct |
| [task](../slots/task.md) | 1 <br/> [String](../types/String.md) | The template asked | direct |
| [condition](../slots/condition.md) | 1 <br/> [Condition](../enums/Condition.md) | The real sequence, or its shuffled copy (the control) | direct |
| [sequence](../slots/sequence.md) | 1 <br/> [String](../types/String.md) | The residues asked (for a shuffled control, the shuffled residues) | direct |
| [seq_md5](../slots/seq_md5.md) | 1 <br/> [String](../types/String.md) | MD5 of the upper-case residues asked, the checksum UniParc uses | direct |
| [sequence_length](../slots/sequence_length.md) | 1 <br/> [Integer](../types/Integer.md) |  | direct |
| [provider](../slots/provider.md) | 1 <br/> [String](../types/String.md) | anthropic, gemini, openai, or stub | direct |
| [model](../slots/model.md) | 1 <br/> [String](../types/String.md) | The model requested | direct |
| [effort](../slots/effort.md) | 1 <br/> [String](../types/String.md) | The effort or thinking level, in the provider's own labels | direct |
| [options](../slots/options.md) | 0..1 <br/> [Any](../classes/Any.md) | Every request field besides the prompt, as sent | direct |
| [client](../slots/client.md) | 0..1 <br/> [String](../types/String.md) | The client library and its version | direct |
| [annotator_version](../slots/annotator_version.md) | 0..1 <br/> [String](../types/String.md) | The peptalk version that made the call | direct |
| [served_model](../slots/served_model.md) | 0..1 <br/> [String](../types/String.md) | The model that answered, as the provider reports it | direct |
| [fallback_used](../slots/fallback_used.md) | 1 <br/> [Boolean](../types/Boolean.md) | True if a server-side fallback model answered instead of the one requested | direct |
| [response_id](../slots/response_id.md) | 0..1 <br/> [String](../types/String.md) | The provider's id for the response | direct |
| [prompt_version](../slots/prompt_version.md) | 1 <br/> [String](../types/String.md) | First 12 hex digits of the SHA-256 of the template's prompt file | direct |
| [prompt_sha256](../slots/prompt_sha256.md) | 1 <br/> [String](../types/String.md) | SHA-256 of the full prompt sent | direct |
| [context](../slots/context.md) | 1 <br/> [HeaderContext](../enums/HeaderContext.md) | How much of the FASTA header the model saw | direct |
| [output](../slots/output.md) | 1 <br/> [OutputMode](../enums/OutputMode.md) | Free text parsed for JSON (the default), or provider structured output | direct |
| [params](../slots/params.md) | 0..1 <br/> [Any](../classes/Any.md) | The template's parameters (ask templates) | direct |
| [payload](../slots/payload.md) | * <br/> [String](../types/String.md) | Optional answer keys asked for (confidence, rationale, evidence, alternatives... | direct |
| [expected](../slots/expected.md) | 0..1 <br/> [Verdict](../enums/Verdict.md) | The verdict a claim expected | direct |
| [note](../slots/note.md) | 0..1 <br/> [String](../types/String.md) | The claim's note | direct |
| [header](../slots/header.md) | 0..1 <br/> [Any](../classes/Any.md) | Every field parsed from the FASTA header (accession, organism, taxon id,  | direct |
| [text](../slots/text.md) | 0..1 <br/> [String](../types/String.md) | The model's reply, verbatim | direct |
| [answer](../slots/answer.md) | 0..1 <br/> [Any](../classes/Any.md) | The answer object parsed from the reply: open-ended, shaped by the template (... | direct |
| [validation_error](../slots/validation_error.md) | 0..1 <br/> [String](../types/String.md) | Why the answer object failed the template's answer model, if it did | direct |
| [stop_reason](../slots/stop_reason.md) | 0..1 <br/> [String](../types/String.md) | Why the model stopped, as the provider reports it; `refusal:<category>` for a... | direct |
| [error](../slots/error.md) | 0..1 <br/> [String](../types/String.md) | Why the call failed, if it did | direct |
| [usage](../slots/usage.md) | 0..1 <br/> [Usage](../classes/Usage.md) | Token counts | direct |
| [expected_input_tokens](../slots/expected_input_tokens.md) | 0..1 <br/> [Integer](../types/Integer.md) | The provider's count of the request alone; checked against the reported input | direct |
| [cost_usd](../slots/cost_usd.md) | 0..1 <br/> [Float](../types/Float.md) | Cost in US dollars at list price, if the model has a price | direct |
| [batch](../slots/batch.md) | 1 <br/> [Boolean](../types/Boolean.md) | True if asked through a provider batch API | direct |
| [batch_id](../slots/batch_id.md) | 0..1 <br/> [String](../types/String.md) | The provider's batch id | direct |
| [cached](../slots/cached.md) | 1 <br/> [Boolean](../types/Boolean.md) | True if this answer was reused from the store instead of asked again | direct |
| [checks](../slots/checks.md) | * <br/> [Check](../classes/Check.md) | The automatic checks of the answer | direct |
| [confidence](../slots/confidence.md) | 1 <br/> [Confidence](../enums/Confidence.md) | peptalk's own result from its checks (not the model's stated confidence, whic... | direct |
| [started_at](../slots/started_at.md) | 1 <br/> [String](../types/String.md) | When the call started (ISO 8601, UTC) | direct |
| [finished_at](../slots/finished_at.md) | 0..1 <br/> [String](../types/String.md) | When the call finished (ISO 8601, UTC) | direct |
| [duration_ms](../slots/duration_ms.md) | 0..1 <br/> [Integer](../types/Integer.md) |  | direct |















## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:Annotation |
| native | peptalk:Annotation |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: Annotation
description: One answer to one task for one sequence, with provenance, checks and
  cost. A reused (cached) answer keeps the uid of the call that produced it, so merged
  exports deduplicate on uid.
from_schema: https://w3id.org/ai4curation/peptalk
attributes:
  uid:
    name: uid
    description: The call that produced the answer.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    identifier: true
    domain_of:
    - Annotation
  id:
    name: id
    description: The first word of the sequence's FASTA header, as given.
    from_schema: https://w3id.org/ai4curation/peptalk
    domain_of:
    - ProteinClaims
    - Claim
    - Annotation
    required: true
  description:
    name: description
    description: The rest of the FASTA header line.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  task:
    name: task
    description: The template asked.
    from_schema: https://w3id.org/ai4curation/peptalk
    domain_of:
    - ClaimBody
    - Annotation
    required: true
  condition:
    name: condition
    description: The real sequence, or its shuffled copy (the control).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: string(real)
    domain_of:
    - Annotation
    range: Condition
    required: true
  sequence:
    name: sequence
    description: The residues asked (for a shuffled control, the shuffled residues).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    required: true
  seq_md5:
    name: seq_md5
    description: MD5 of the upper-case residues asked, the checksum UniParc uses.
      The key to the sequence.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    required: true
  sequence_length:
    name: sequence_length
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: integer
    required: true
  provider:
    name: provider
    description: anthropic, gemini, openai, or stub.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    required: true
  model:
    name: model
    description: The model requested.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    required: true
  effort:
    name: effort
    description: The effort or thinking level, in the provider's own labels.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    required: true
  options:
    name: options
    description: Every request field besides the prompt, as sent.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: Any
  client:
    name: client
    description: The client library and its version.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  annotator_version:
    name: annotator_version
    description: The peptalk version that made the call.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  served_model:
    name: served_model
    description: The model that answered, as the provider reports it.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  fallback_used:
    name: fallback_used
    description: True if a server-side fallback model answered instead of the one
      requested.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: 'False'
    domain_of:
    - Annotation
    range: boolean
    required: true
  response_id:
    name: response_id
    description: The provider's id for the response.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  prompt_version:
    name: prompt_version
    description: First 12 hex digits of the SHA-256 of the template's prompt file.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    required: true
  prompt_sha256:
    name: prompt_sha256
    description: SHA-256 of the full prompt sent.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    required: true
  context:
    name: context
    description: How much of the FASTA header the model saw.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: string(blind)
    domain_of:
    - Annotation
    range: HeaderContext
    required: true
  output:
    name: output
    description: Free text parsed for JSON (the default), or provider structured output.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: string(text)
    domain_of:
    - Annotation
    range: OutputMode
    required: true
  params:
    name: params
    description: The template's parameters (ask templates).
    from_schema: https://w3id.org/ai4curation/peptalk
    domain_of:
    - ClaimBody
    - Annotation
    range: Any
  payload:
    name: payload
    description: Optional answer keys asked for (confidence, rationale, evidence,
      alternatives).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    multivalued: true
  expected:
    name: expected
    description: The verdict a claim expected. Never sent to the model.
    from_schema: https://w3id.org/ai4curation/peptalk
    domain_of:
    - ClaimBody
    - Annotation
    range: Verdict
  note:
    name: note
    description: The claim's note. Never sent to the model.
    from_schema: https://w3id.org/ai4curation/peptalk
    domain_of:
    - ClaimBody
    - Annotation
  header:
    name: header
    description: Every field parsed from the FASTA header (accession, organism, taxon
      id, ...).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: Any
  text:
    name: text
    description: The model's reply, verbatim.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  answer:
    name: answer
    description: 'The answer object parsed from the reply: open-ended, shaped by the
      template (its JSON Schema is `peptalk tasks --schema TASK`).'
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: Any
  validation_error:
    name: validation_error
    description: Why the answer object failed the template's answer model, if it did.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  stop_reason:
    name: stop_reason
    description: Why the model stopped, as the provider reports it; `refusal:<category>`
      for a refusal.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  error:
    name: error
    description: Why the call failed, if it did.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  usage:
    name: usage
    description: Token counts.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: Usage
    inlined: true
  expected_input_tokens:
    name: expected_input_tokens
    description: The provider's count of the request alone; checked against the reported
      input.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: integer
  cost_usd:
    name: cost_usd
    description: Cost in US dollars at list price, if the model has a price.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: float
  batch:
    name: batch
    description: True if asked through a provider batch API.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: 'False'
    domain_of:
    - Annotation
    range: boolean
    required: true
  batch_id:
    name: batch_id
    description: The provider's batch id.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  cached:
    name: cached
    description: True if this answer was reused from the store instead of asked again.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: 'False'
    domain_of:
    - Annotation
    range: boolean
    required: true
  checks:
    name: checks
    description: The automatic checks of the answer.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: Check
    multivalued: true
    inlined_as_list: true
  confidence:
    name: confidence
    description: peptalk's own result from its checks (not the model's stated confidence,
      which is in the answer).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: string(no_answer)
    domain_of:
    - Annotation
    range: Confidence
    required: true
  started_at:
    name: started_at
    description: When the call started (ISO 8601, UTC).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    required: true
  finished_at:
    name: finished_at
    description: When the call finished (ISO 8601, UTC).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
  duration_ms:
    name: duration_ms
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - Annotation
    range: integer

```
</details>

### Induced

<details>
```yaml
name: Annotation
description: One answer to one task for one sequence, with provenance, checks and
  cost. A reused (cached) answer keeps the uid of the call that produced it, so merged
  exports deduplicate on uid.
from_schema: https://w3id.org/ai4curation/peptalk
attributes:
  uid:
    name: uid
    description: The call that produced the answer.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    identifier: true
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  id:
    name: id
    description: The first word of the sequence's FASTA header, as given.
    from_schema: https://w3id.org/ai4curation/peptalk
    owner: Annotation
    domain_of:
    - ProteinClaims
    - Claim
    - Annotation
    range: string
    required: true
  description:
    name: description
    description: The rest of the FASTA header line.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  task:
    name: task
    description: The template asked.
    from_schema: https://w3id.org/ai4curation/peptalk
    owner: Annotation
    domain_of:
    - ClaimBody
    - Annotation
    range: string
    required: true
  condition:
    name: condition
    description: The real sequence, or its shuffled copy (the control).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: string(real)
    owner: Annotation
    domain_of:
    - Annotation
    range: Condition
    required: true
  sequence:
    name: sequence
    description: The residues asked (for a shuffled control, the shuffled residues).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  seq_md5:
    name: seq_md5
    description: MD5 of the upper-case residues asked, the checksum UniParc uses.
      The key to the sequence.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  sequence_length:
    name: sequence_length
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: integer
    required: true
  provider:
    name: provider
    description: anthropic, gemini, openai, or stub.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  model:
    name: model
    description: The model requested.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  effort:
    name: effort
    description: The effort or thinking level, in the provider's own labels.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  options:
    name: options
    description: Every request field besides the prompt, as sent.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: Any
  client:
    name: client
    description: The client library and its version.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  annotator_version:
    name: annotator_version
    description: The peptalk version that made the call.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  served_model:
    name: served_model
    description: The model that answered, as the provider reports it.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  fallback_used:
    name: fallback_used
    description: True if a server-side fallback model answered instead of the one
      requested.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: 'False'
    owner: Annotation
    domain_of:
    - Annotation
    range: boolean
    required: true
  response_id:
    name: response_id
    description: The provider's id for the response.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  prompt_version:
    name: prompt_version
    description: First 12 hex digits of the SHA-256 of the template's prompt file.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  prompt_sha256:
    name: prompt_sha256
    description: SHA-256 of the full prompt sent.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  context:
    name: context
    description: How much of the FASTA header the model saw.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: string(blind)
    owner: Annotation
    domain_of:
    - Annotation
    range: HeaderContext
    required: true
  output:
    name: output
    description: Free text parsed for JSON (the default), or provider structured output.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: string(text)
    owner: Annotation
    domain_of:
    - Annotation
    range: OutputMode
    required: true
  params:
    name: params
    description: The template's parameters (ask templates).
    from_schema: https://w3id.org/ai4curation/peptalk
    owner: Annotation
    domain_of:
    - ClaimBody
    - Annotation
    range: Any
  payload:
    name: payload
    description: Optional answer keys asked for (confidence, rationale, evidence,
      alternatives).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    multivalued: true
  expected:
    name: expected
    description: The verdict a claim expected. Never sent to the model.
    from_schema: https://w3id.org/ai4curation/peptalk
    owner: Annotation
    domain_of:
    - ClaimBody
    - Annotation
    range: Verdict
  note:
    name: note
    description: The claim's note. Never sent to the model.
    from_schema: https://w3id.org/ai4curation/peptalk
    owner: Annotation
    domain_of:
    - ClaimBody
    - Annotation
    range: string
  header:
    name: header
    description: Every field parsed from the FASTA header (accession, organism, taxon
      id, ...).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: Any
  text:
    name: text
    description: The model's reply, verbatim.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  answer:
    name: answer
    description: 'The answer object parsed from the reply: open-ended, shaped by the
      template (its JSON Schema is `peptalk tasks --schema TASK`).'
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: Any
  validation_error:
    name: validation_error
    description: Why the answer object failed the template's answer model, if it did.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  stop_reason:
    name: stop_reason
    description: Why the model stopped, as the provider reports it; `refusal:<category>`
      for a refusal.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  error:
    name: error
    description: Why the call failed, if it did.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  usage:
    name: usage
    description: Token counts.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: Usage
    inlined: true
  expected_input_tokens:
    name: expected_input_tokens
    description: The provider's count of the request alone; checked against the reported
      input.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: integer
  cost_usd:
    name: cost_usd
    description: Cost in US dollars at list price, if the model has a price.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: float
  batch:
    name: batch
    description: True if asked through a provider batch API.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: 'False'
    owner: Annotation
    domain_of:
    - Annotation
    range: boolean
    required: true
  batch_id:
    name: batch_id
    description: The provider's batch id.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  cached:
    name: cached
    description: True if this answer was reused from the store instead of asked again.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: 'False'
    owner: Annotation
    domain_of:
    - Annotation
    range: boolean
    required: true
  checks:
    name: checks
    description: The automatic checks of the answer.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: Check
    multivalued: true
    inlined: true
    inlined_as_list: true
  confidence:
    name: confidence
    description: peptalk's own result from its checks (not the model's stated confidence,
      which is in the answer).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    ifabsent: string(no_answer)
    owner: Annotation
    domain_of:
    - Annotation
    range: Confidence
    required: true
  started_at:
    name: started_at
    description: When the call started (ISO 8601, UTC).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
    required: true
  finished_at:
    name: finished_at
    description: When the call finished (ISO 8601, UTC).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: string
  duration_ms:
    name: duration_ms
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: Annotation
    domain_of:
    - Annotation
    range: integer

```
</details></div>