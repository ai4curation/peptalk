---
search:
  boost: 2.0
---


# Enum: OutputMode 



<div data-search-exclude markdown="1">

URI: [peptalk:enum/OutputMode](https://w3id.org/ai4curation/peptalk/enum/OutputMode)

## Permissible Values
| Value | Meaning | Description |
| --- | --- | --- |
| text | None | JSON asked for in plain text, then parsed |
| json_schema | None | Provider structured output constrained to the template's JSON Schema |




## Slots

| Name | Description |
| ---  | --- |
| [output](../slots/output.md) | Free text parsed for JSON (the default), or provider structured output |










## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk






## LinkML Source

<details>
```yaml
name: OutputMode
from_schema: https://w3id.org/ai4curation/peptalk
rank: 1000
permissible_values:
  text:
    text: text
    description: JSON asked for in plain text, then parsed.
  json_schema:
    text: json_schema
    description: Provider structured output constrained to the template's JSON Schema.

```
</details>

</div>