---
search:
  boost: 5.0
---

# Slot: answer 


_The answer object parsed from the reply: open-ended, shaped by the template (its JSON Schema is `peptalk tasks --schema TASK`)._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/answer](https://w3id.org/ai4curation/peptalk/slot/answer)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Any](../classes/Any.md) |
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
| self | peptalk:answer |
| native | peptalk:answer |




## LinkML Source

<details>
```yaml
name: answer
description: 'The answer object parsed from the reply: open-ended, shaped by the template
  (its JSON Schema is `peptalk tasks --schema TASK`).'
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: Any

```
</details></div>