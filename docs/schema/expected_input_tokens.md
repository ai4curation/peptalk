---
search:
  boost: 5.0
---

# Slot: expected_input_tokens 


_The provider's count of the request alone; checked against the reported input._



<div data-search-exclude markdown="1">



URI: [peptalk:expected_input_tokens](https://w3id.org/ai4curation/peptalk/expected_input_tokens)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Integer](Integer.md) |
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
| self | peptalk:expected_input_tokens |
| native | peptalk:expected_input_tokens |




## LinkML Source

<details>
```yaml
name: expected_input_tokens
description: The provider's count of the request alone; checked against the reported
  input.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: integer

```
</details></div>