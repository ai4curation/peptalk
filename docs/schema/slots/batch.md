---
search:
  boost: 5.0
---

# Slot: batch 


_True if asked through a provider batch API._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/batch](https://w3id.org/ai4curation/peptalk/slot/batch)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Boolean](../types/Boolean.md) |
| Domain Of | [Annotation](../classes/Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `False` |
| Owner | [Annotation](../classes/Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:batch |
| native | peptalk:batch |




## LinkML Source

<details>
```yaml
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

```
</details></div>