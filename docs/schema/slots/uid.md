---
search:
  boost: 5.0
---

# Slot: uid 


_The call that produced the answer._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/uid](https://w3id.org/ai4curation/peptalk/slot/uid)
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
| Identifier | Yes |
| Owner | [Annotation](../classes/Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:uid |
| native | peptalk:uid |




## LinkML Source

<details>
```yaml
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

```
</details></div>