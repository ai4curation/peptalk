---
search:
  boost: 5.0
---

# Slot: stop_reason 


_Why the model stopped, as the provider reports it; `refusal:<category>` for a refusal._



<div data-search-exclude markdown="1">



URI: [peptalk:stop_reason](https://w3id.org/ai4curation/peptalk/stop_reason)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [Annotation](Annotation.md) |
### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [Annotation](Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:stop_reason |
| native | peptalk:stop_reason |




## LinkML Source

<details>
```yaml
name: stop_reason
description: Why the model stopped, as the provider reports it; `refusal:<category>`
  for a refusal.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string

```
</details></div>