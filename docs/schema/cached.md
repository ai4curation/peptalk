---
search:
  boost: 5.0
---

# Slot: cached 


_True if this answer was reused from the store instead of asked again._



<div data-search-exclude markdown="1">



URI: [peptalk:cached](https://w3id.org/ai4curation/peptalk/cached)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Boolean](Boolean.md) |
| Domain Of | [Annotation](Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `False` |
| Owner | [Annotation](Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:cached |
| native | peptalk:cached |




## LinkML Source

<details>
```yaml
name: cached
description: True if this answer was reused from the store instead of asked again.
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