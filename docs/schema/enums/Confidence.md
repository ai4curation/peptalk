---
search:
  boost: 2.0
---


# Enum: Confidence 



<div data-search-exclude markdown="1">

URI: [peptalk:enum/Confidence](https://w3id.org/ai4curation/peptalk/enum/Confidence)

## Permissible Values
| Value | Meaning | Description |
| --- | --- | --- |
| checks_passed | None | Every check passed (which says nothing more) |
| flagged | None | At least one check failed |
| no_answer | None | The call failed, was refused, or gave no valid answer object |




## Slots

| Name | Description |
| ---  | --- |
| [confidence](../slots/confidence.md) | peptalk's own result from its checks (not the model's stated confidence, whic... |










## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk






## LinkML Source

<details>
```yaml
name: Confidence
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
permissible_values:
  checks_passed:
    text: checks_passed
    description: Every check passed (which says nothing more).
  flagged:
    text: flagged
    description: At least one check failed.
  no_answer:
    text: no_answer
    description: The call failed, was refused, or gave no valid answer object.

```
</details>

</div>