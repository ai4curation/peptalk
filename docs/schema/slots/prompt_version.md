---
search:
  boost: 5.0
---

# Slot: prompt_version 


_First 12 hex digits of the SHA-256 of the template's prompt file._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/prompt_version](https://w3id.org/ai4curation/peptalk/slot/prompt_version)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](../types/String.md) |
| Domain Of | [Annotation](../classes/Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [Annotation](../classes/Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:prompt_version |
| native | peptalk:prompt_version |




## LinkML Source

<details>
```yaml
name: prompt_version
description: First 12 hex digits of the SHA-256 of the template's prompt file.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string
required: true

```
</details></div>