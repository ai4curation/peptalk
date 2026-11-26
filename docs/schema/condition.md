---
search:
  boost: 2.0
---


# Enum: Condition 



<div data-search-exclude markdown="1">

URI: [peptalk:Condition](https://w3id.org/ai4curation/peptalk/Condition)

## Permissible Values
| Value | Meaning | Description |
| --- | --- | --- |
| real | None | The sequence as given |
| shuffled | None | A shuffled copy of it, the control |




## Slots

| Name | Description |
| ---  | --- |
| [condition](condition.md) | The real sequence, or its shuffled copy (the control) |










## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk






## LinkML Source

<details>
```yaml
name: Condition
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
permissible_values:
  real:
    text: real
    description: The sequence as given.
  shuffled:
    text: shuffled
    description: A shuffled copy of it, the control.

```
</details>

</div>