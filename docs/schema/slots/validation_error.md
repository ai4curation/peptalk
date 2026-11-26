---
search:
  boost: 5.0
---

# Slot: validation_error 


_Why the answer object failed the template's answer model, if it did._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/validation_error](https://w3id.org/ai4curation/peptalk/slot/validation_error)
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
| self | peptalk:validation_error |
| native | peptalk:validation_error |




## LinkML Source

<details>
```yaml
name: validation_error
description: Why the answer object failed the template's answer model, if it did.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string

```
</details></div>