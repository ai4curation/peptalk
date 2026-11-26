---
search:
  boost: 5.0
---

# Slot: served_model 


_The model that answered, as the provider reports it._



<div data-search-exclude markdown="1">



URI: [peptalk:served_model](https://w3id.org/ai4curation/peptalk/served_model)
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
| self | peptalk:served_model |
| native | peptalk:served_model |




## LinkML Source

<details>
```yaml
name: served_model
description: The model that answered, as the provider reports it.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string

```
</details></div>