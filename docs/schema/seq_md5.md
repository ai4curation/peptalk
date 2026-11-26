---
search:
  boost: 5.0
---

# Slot: seq_md5 


_MD5 of the upper-case residues asked, the checksum UniParc uses. The key to the sequence._



<div data-search-exclude markdown="1">



URI: [peptalk:seq_md5](https://w3id.org/ai4curation/peptalk/seq_md5)
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
### Cardinality and Requirements

| Property | Value |
| --- | --- |
| Required | Yes |


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
| self | peptalk:seq_md5 |
| native | peptalk:seq_md5 |




## LinkML Source

<details>
```yaml
name: seq_md5
description: MD5 of the upper-case residues asked, the checksum UniParc uses. The
  key to the sequence.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string
required: true

```
</details></div>