---
search:
  boost: 5.0
---

# Slot: task 

<div data-search-exclude markdown="1">



URI: [peptalk:task](https://w3id.org/ai4curation/peptalk/task)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ClaimBody](ClaimBody.md) | One claim, without the protein it is about (as written under a protein) |  no  |
| [Claim](Claim.md) | One claim about one protein |  no  |
| [Annotation](Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [ClaimBody](ClaimBody.md), [Annotation](Annotation.md) |










## Identifier and Mapping Information






## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:task |
| native | peptalk:task |




## LinkML Source

<details>
```yaml
name: task
domain_of:
- ClaimBody
- Annotation
range: string

```
</details></div>