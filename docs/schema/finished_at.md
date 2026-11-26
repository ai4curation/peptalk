---
search:
  boost: 5.0
---

# Slot: finished_at 


_When the call finished (ISO 8601, UTC)._



<div data-search-exclude markdown="1">



URI: [peptalk:finished_at](https://w3id.org/ai4curation/peptalk/finished_at)
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
| self | peptalk:finished_at |
| native | peptalk:finished_at |




## LinkML Source

<details>
```yaml
name: finished_at
description: When the call finished (ISO 8601, UTC).
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string

```
</details></div>