---
search:
  boost: 5.0
---

# Slot: context 


_How much of the FASTA header the model saw._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/context](https://w3id.org/ai4curation/peptalk/slot/context)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [HeaderContext](../enums/HeaderContext.md) |
| Domain Of | [Annotation](../classes/Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `string(blind)` |
| Owner | [Annotation](../classes/Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:context |
| native | peptalk:context |




## LinkML Source

<details>
```yaml
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

```
</details></div>