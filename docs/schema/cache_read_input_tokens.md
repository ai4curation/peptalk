---
search:
  boost: 5.0
---

# Slot: cache_read_input_tokens 

<div data-search-exclude markdown="1">



URI: [peptalk:cache_read_input_tokens](https://w3id.org/ai4curation/peptalk/cache_read_input_tokens)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Usage](Usage.md) | Token counts for one call |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [Integer](Integer.md) |
| Domain Of | [Usage](Usage.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| If Absent | `int(0)` |
| Owner | [Usage](Usage.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:cache_read_input_tokens |
| native | peptalk:cache_read_input_tokens |




## LinkML Source

<details>
```yaml
name: cache_read_input_tokens
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