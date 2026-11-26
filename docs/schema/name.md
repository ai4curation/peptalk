---
search:
  boost: 5.0
---

# Slot: name 

<div data-search-exclude markdown="1">



URI: [peptalk:name](https://w3id.org/ai4curation/peptalk/name)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [Check](Check.md) | One automatic check of an answer against the sequence, the claim or the shuff... |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [Check](Check.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [Check](Check.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:name |
| native | peptalk:name |




## LinkML Source

<details>
```yaml
name: name
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Check
domain_of:
- Check
range: string
required: true

```
</details></div>