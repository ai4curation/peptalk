---
search:
  boost: 5.0
---

# Slot: model 


_The model requested._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/model](https://w3id.org/ai4curation/peptalk/slot/model)
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
| self | peptalk:model |
| native | peptalk:model |




## LinkML Source

<details>
```yaml
name: model
description: The model requested.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string
required: true

```
</details></div>