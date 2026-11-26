---
search:
  boost: 5.0
---

# Slot: checks 


_The automatic checks of the answer._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/checks](https://w3id.org/ai4curation/peptalk/slot/checks)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Check](../classes/Check.md) |
| Domain Of | [Annotation](../classes/Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |


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
| self | peptalk:checks |
| native | peptalk:checks |




## LinkML Source

<details>
```yaml
name: checks
description: The automatic checks of the answer.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: Check
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>