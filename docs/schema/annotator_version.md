---
search:
  boost: 5.0
---

# Slot: annotator_version 


_The peptalk version that made the call._



<div data-search-exclude markdown="1">



URI: [peptalk:annotator_version](https://w3id.org/ai4curation/peptalk/annotator_version)
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
| self | peptalk:annotator_version |
| native | peptalk:annotator_version |




## LinkML Source

<details>
```yaml
name: annotator_version
description: The peptalk version that made the call.
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
owner: Annotation
domain_of:
- Annotation
range: string

```
</details></div>