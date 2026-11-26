---
search:
  boost: 5.0
---

# Slot: params 

<div data-search-exclude markdown="1">



URI: [peptalk:slot/params](https://w3id.org/ai4curation/peptalk/slot/params)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ClaimBody](../classes/ClaimBody.md) | One claim, without the protein it is about (as written under a protein) |  no  |
| [Claim](../classes/Claim.md) | One claim about one protein |  no  |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](../types/String.md) |
| Domain Of | [ClaimBody](../classes/ClaimBody.md), [Annotation](../classes/Annotation.md) |










## Identifier and Mapping Information






## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:params |
| native | peptalk:params |




## LinkML Source

<details>
```yaml
name: params
domain_of:
- ClaimBody
- Annotation
range: string

```
</details></div>