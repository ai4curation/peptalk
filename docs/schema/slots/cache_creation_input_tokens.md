---
search:
  boost: 5.0
---

# Slot: cache_creation_input_tokens 

<div data-search-exclude markdown="1">



URI: [peptalk:slot/cache_creation_input_tokens](https://w3id.org/ai4curation/peptalk/slot/cache_creation_input_tokens)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Usage](../classes/Usage.md) | Token counts for one call |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Integer](../types/Integer.md) |
| Domain Of | [Usage](../classes/Usage.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `int(0)` |
| Owner | [Usage](../classes/Usage.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:cache_creation_input_tokens |
| native | peptalk:cache_creation_input_tokens |




## LinkML Source

<details>
```yaml
name: cache_creation_input_tokens
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
ifabsent: int(0)
owner: Usage
domain_of:
- Usage
range: integer
required: true

```
</details></div>