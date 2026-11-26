---
search:
  boost: 5.0
---

# Slot: output 


_Free text parsed for JSON (the default), or provider structured output._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/output](https://w3id.org/ai4curation/peptalk/slot/output)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [OutputMode](../enums/OutputMode.md) |
| Domain Of | [Annotation](../classes/Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `string(text)` |
| Owner | [Annotation](../classes/Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:output |
| native | peptalk:output |




## LinkML Source

<details>
```yaml
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

```
</details></div>