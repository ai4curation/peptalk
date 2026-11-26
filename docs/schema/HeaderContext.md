---
search:
  boost: 2.0
---


# Enum: HeaderContext 



<div data-search-exclude markdown="1">

URI: [peptalk:HeaderContext](https://w3id.org/ai4curation/peptalk/HeaderContext)

## Permissible Values
| Value | Meaning | Description |
| --- | --- | --- |
| blind | None | The model saw '>sequence' only (the fs2f protocol) |
| organism | None | The model saw the organism and taxon id from the header |
| full | None | The model saw the whole header line |




## Slots

| Name | Description |
| ---  | --- |
| [context](context.md) | How much of the FASTA header the model saw |










## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk






## LinkML Source

<details>
```yaml
name: HeaderContext
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
permissible_values:
  blind:
    text: blind
    description: The model saw '>sequence' only (the fs2f protocol).
  organism:
    text: organism
    description: The model saw the organism and taxon id from the header.
  full:
    text: full
    description: The model saw the whole header line.

```
</details>

</div>