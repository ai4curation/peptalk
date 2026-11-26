---
search:
  boost: 5.0
---

# Slot: cost_usd 


_Cost in US dollars at list price, if the model has a price._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/cost_usd](https://w3id.org/ai4curation/peptalk/slot/cost_usd)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Float](../types/Float.md) |
| Domain Of | [Annotation](../classes/Annotation.md) |
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
| self | peptalk:cost_usd |
| native | peptalk:cost_usd |




## LinkML Source

<details>
```yaml
name: cost_usd
description: Cost in US dollars at list price, if the model has a price.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: float

```
</details></div>