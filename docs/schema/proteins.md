---
search:
  boost: 5.0
---

# Slot: proteins 


_Claims grouped by protein._



<div data-search-exclude markdown="1">



URI: [peptalk:proteins](https://w3id.org/ai4curation/peptalk/proteins)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ClaimsFile](ClaimsFile.md) | A claims file |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [ProteinClaims](ProteinClaims.md) |
| Domain Of | [ClaimsFile](ClaimsFile.md) |
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Multivalued | Yes |


### Slot Characteristics

| Property | Value |
| --- | --- |
| Owner | [ClaimsFile](ClaimsFile.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:proteins |
| native | peptalk:proteins |




## LinkML Source

<details>
```yaml
name: proteins
description: Claims grouped by protein.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: ClaimsFile
domain_of:
- ClaimsFile
range: ProteinClaims
multivalued: true
inlined: true
inlined_as_list: true

```
</details></div>