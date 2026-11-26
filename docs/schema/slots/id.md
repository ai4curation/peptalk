---
search:
  boost: 5.0
---

# Slot: id 

<div data-search-exclude markdown="1">



URI: [peptalk:slot/id](https://w3id.org/ai4curation/peptalk/slot/id)
<!-- no inheritance hierarchy -->





## Applicable Classes

| Name | Description | Modifies Slot |
| --- | --- | --- |
| [ProteinClaims](../classes/ProteinClaims.md) | The claims about one protein |  no  |
| [Claim](../classes/Claim.md) | One claim about one protein |  no  |
| [Annotation](../classes/Annotation.md) | One answer to one task for one sequence, with provenance, checks and cost |  no  |






## Properties

### Type and Range

| Property | Value |
| --- | --- |
| Range | [String](../types/String.md) |
| Domain Of | [ProteinClaims](../classes/ProteinClaims.md), [Claim](../classes/Claim.md), [Annotation](../classes/Annotation.md) |










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