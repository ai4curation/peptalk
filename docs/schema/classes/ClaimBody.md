---
search:
  boost: 10.0
---

# Class: ClaimBody 


_One claim, without the protein it is about (as written under a protein)._



<div data-search-exclude markdown="1">



URI: [peptalk:class/ClaimBody](https://w3id.org/ai4curation/peptalk/class/ClaimBody)





```mermaid
 classDiagram
    class ClaimBody
    click ClaimBody href "../../classes/ClaimBody/"
      ClaimBody <|-- Claim
        click Claim href "../../classes/Claim/"
      
      ClaimBody : expected
        
          
    
        
        
        ClaimBody --> "0..1" Verdict : expected
        click Verdict href "../../enums/Verdict/"
    

        
      ClaimBody : note
        
      ClaimBody : params
        
          
    
        
        
        ClaimBody --> "0..1" Any : params
        click Any href "../../classes/Any/"
    

        
      ClaimBody : task
        
      
```





## Inheritance
* **ClaimBody**
    * [Claim](../classes/Claim.md)


## Slots

| Name | Cardinality and Range | Description | Inheritance |
| ---  | --- | --- | --- |
| [task](../slots/task.md) | 1 <br/> [String](../types/String.md) | The ask template that puts the claim to the model, such as ask-catalytic-resi... | direct |
| [params](../slots/params.md) | 0..1 <br/> [Any](../classes/Any.md) | The template's parameters, all of them and no others, such as {position: 436,... | direct |
| [expected](../slots/expected.md) | 0..1 <br/> [Verdict](../enums/Verdict.md) | The verdict you expect, for benchmarks | direct |
| [note](../slots/note.md) | 0..1 <br/> [String](../types/String.md) | Any text | direct |





## Usages

| used by | used in | type | used |
| ---  | --- | --- | --- |
| [ProteinClaims](../classes/ProteinClaims.md) | [claims](../slots/claims.md) | range | [ClaimBody](../classes/ClaimBody.md) |












## Identifier and Mapping Information





### Schema Source


* from schema: https://w3id.org/ai4curation/peptalk




## Mappings

| Mapping Type | Mapped Value |
| ---  | ---  |
| self | peptalk:ClaimBody |
| native | peptalk:ClaimBody |






## LinkML Source

<!-- TODO: investigate https://stackoverflow.com/questions/37606292/how-to-create-tabbed-code-blocks-in-mkdocs-or-sphinx -->

### Direct

<details>
```yaml
name: ClaimBody
description: One claim, without the protein it is about (as written under a protein).
from_schema: https://w3id.org/ai4curation/peptalk
attributes:
  task:
    name: task
    description: The ask template that puts the claim to the model, such as ask-catalytic-residue
      (`peptalk tasks --ask` lists them).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - ClaimBody
    - Annotation
    required: true
  params:
    name: params
    description: 'The template''s parameters, all of them and no others, such as {position:
      436, residue: D}. Values may be written as numbers; they are read as text.'
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - ClaimBody
    - Annotation
    range: Any
  expected:
    name: expected
    description: The verdict you expect, for benchmarks. Never sent to the model and
      not part of the cache key.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - ClaimBody
    - Annotation
    range: Verdict
  note:
    name: note
    description: Any text. Kept with the result, never sent to the model.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    domain_of:
    - ClaimBody
    - Annotation

```
</details>

### Induced

<details>
```yaml
name: ClaimBody
description: One claim, without the protein it is about (as written under a protein).
from_schema: https://w3id.org/ai4curation/peptalk
attributes:
  task:
    name: task
    description: The ask template that puts the claim to the model, such as ask-catalytic-residue
      (`peptalk tasks --ask` lists them).
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: ClaimBody
    domain_of:
    - ClaimBody
    - Annotation
    range: string
    required: true
  params:
    name: params
    description: 'The template''s parameters, all of them and no others, such as {position:
      436, residue: D}. Values may be written as numbers; they are read as text.'
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: ClaimBody
    domain_of:
    - ClaimBody
    - Annotation
    range: Any
  expected:
    name: expected
    description: The verdict you expect, for benchmarks. Never sent to the model and
      not part of the cache key.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: ClaimBody
    domain_of:
    - ClaimBody
    - Annotation
    range: Verdict
  note:
    name: note
    description: Any text. Kept with the result, never sent to the model.
    from_schema: https://w3id.org/ai4curation/peptalk
    rank: 1000
    owner: ClaimBody
    domain_of:
    - ClaimBody
    - Annotation
    range: string

```
</details></div>