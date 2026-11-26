---
search:
  boost: 5.0
---

# Slot: prompt_sha256 


_SHA-256 of the full prompt sent._



<div data-search-exclude markdown="1">



URI: [peptalk:prompt_sha256](https://w3id.org/ai4curation/peptalk/prompt_sha256)
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
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


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
| self | peptalk:prompt_sha256 |
| native | peptalk:prompt_sha256 |




## LinkML Source

<details>
```yaml
name: prompt_sha256
description: SHA-256 of the full prompt sent.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string
required: true

```
</details></div>