---
search:
  boost: 5.0
---

# Slot: header 


_Every field parsed from the FASTA header (accession, organism, taxon id, ...)._



<div data-search-exclude markdown="1">



URI: [peptalk:slot/header](https://w3id.org/ai4curation/peptalk/slot/header)
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
| self | peptalk:header |
| native | peptalk:header |




## LinkML Source

<details>
```yaml
name: header
description: Every field parsed from the FASTA header (accession, organism, taxon
  id, ...).
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: Any

```
</details></div>