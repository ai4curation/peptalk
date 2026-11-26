---
search:
  boost: 5.0
---

# Slot: confidence 


_peptalk's own result from its checks (not the model's stated confidence, which is in the answer)._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/confidence](https://w3id.org/ai4curation/peptalk/slot/confidence)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Confidence](../enums/Confidence.md) |
| Domain Of | [Annotation](../classes/Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `string(no_answer)` |
| Owner | [Annotation](../classes/Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:confidence |
| native | peptalk:confidence |




## LinkML Source

<details>
```yaml
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

```
</details></div>