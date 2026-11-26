---
search:
  boost: 5.0
---

# Slot: condition 


_The real sequence, or its shuffled copy (the control)._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/condition](https://w3id.org/ai4curation/peptalk/slot/condition)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Condition](../enums/Condition.md) |
| Domain Of | [Annotation](../classes/Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `string(real)` |
| Owner | [Annotation](../classes/Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:condition |
| native | peptalk:condition |




## LinkML Source

<details>
```yaml
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

```
</details></div>