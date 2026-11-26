---
search:
  boost: 5.0
---

# Slot: id 

<div data-search-exclude markdown="1">



URI: [peptalk:id](https://w3id.org/ai4curation/peptalk/id)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ProteinClaims](ProteinClaims.md) | The claims about one protein |  no  |
| [Claim](Claim.md) | One claim about one protein |  no  |
| [Annotation](Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](String.md) |
| Domain Of | [ProteinClaims](ProteinClaims.md), [Claim](Claim.md), [Annotation](Annotation.md) |










## Identifier and Mapping Information






## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:id |
| native | peptalk:id |




## LinkML Source

<details>
```yaml
name: id
domain_of:
- ProteinClaims
- Claim
- Annotation
range: string

```
</details></div>