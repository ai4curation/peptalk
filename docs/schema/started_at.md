---
search:
  boost: 5.0
---

# Slot: started_at 


_When the call started (ISO 8601, UTC)._



<div data-search-exclude markdown="1">



URI: [peptalk:started_at](https://w3id.org/ai4curation/peptalk/started_at)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [Annotation](Annotation.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [Annotation](Annotation.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:started_at |
| native | peptalk:started_at |




## LinkML Source

<details>
```yaml
name: started_at
description: When the call started (ISO 8601, UTC).
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string
required: true

```
</details></div>