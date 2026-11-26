# Writing a template

A template is a prompt plus a schema: what one task asks, and what the answer must look like. A little Python
says how peptalk checks the answer. This page walks through the `localization` template that ships with peptalk,
from an empty directory to a tested task. The design is in [design.md](design.md#4-templates).

## 1. Make the directory

```
src/peptalk/templates/localization/
    prompt.txt              # what the task asks                          (you write)
    schema.yaml             # the answer, in LinkML                       (you write)
    __init__.py             # checks, control, GFF3 features; registers   (you write)
    schema.py               # Pydantic answer models                      (generated)
    Answer.schema.json      # JSON Schema of the answer                   (generated)
```

## 2. Write the prompt

`prompt.txt` is the whole prompt, with placeholders that peptalk fills in. Its final newline is dropped.

```text
Below is a protein sequence in one-letter amino acid codes. {{Basis}}, predict where the protein is located in
the cell and which targeting signals it carries. Reply with a single JSON object and nothing else, with these
keys: "localization": list of compartment names, most likely first ...; "targeting_signals": list of {"type": ...,
"start": int, "end": int} (1-based residue positions; empty list if none); "transmembrane_helices": list of
[start, end]; "protein_name": string; "recognised": true if you recognise this as a specific known protein, else
false; "reason": one or two sentences.{{payload}}

>{{header}}
{{sequence}}
```

(The real file has the instruction on one line.) The placeholders are:

| Placeholder | Becomes |
|---|---|
| `{{basis}}` / `{{Basis}}` | the context wording: "using only the sequence" (blind), "using the sequence and the organism given in its header", or "using the sequence and the information in its FASTA header" |
| `{{payload}}` | nothing, or " Also include these keys: ..." for the payload the user asked for (`--with`); put it right after the key list |
| `{{header}}` | the header line the model sees at the context level (`sequence` when blind) |
| `{{sequence}}` | the residues, 60 per line |
| `{{anything_else}}` | a parameter of the template (declare it in `params`; see ask templates below) |

`{{header}}` and `{{sequence}}` are required. Ask for JSON in plain text and name every key with its type. That
is the protocol peptalk parses by default. Provider structured output is opt-in and uses the schema from step 3.

## 3. Write the answer schema in LinkML

`schema.yaml` defines the answer in [LinkML](https://linkml.io). It is the single source of truth: the Pydantic
model that validates replies and the JSON Schema that opt-in structured output sends are both generated from it.

```yaml
id: https://w3id.org/ai4curation/peptalk/templates/localization
name: peptalk_localization
prefixes:
  linkml: https://w3id.org/linkml/
  peptalk: https://w3id.org/ai4curation/peptalk/
default_prefix: peptalk
default_range: string
imports:
  - linkml:types
  - peptalk_common              # shared building blocks (src/peptalk/templates/common.yaml)

classes:
  TargetingSignal:
    attributes:
      type:
        description: signal peptide, mitochondrial transit peptide, ... or other.
      start:
        range: integer
      end:
        range: integer
  Answer:
    is_a: AnswerBase            # adds the optional payload keys: confidence, rationale, evidence, alternatives
    annotations:
      answer: true              # marks the class(es) a prompt asks for
    slots:
      - transmembrane_helices   # [start, end] pairs, from peptalk_common
    attributes:
      localization:
        description: Compartment names, most likely first.
        multivalued: true
      targeting_signals:
        range: TargetingSignal
        multivalued: true
        inlined_as_list: true
      protein_name:
      recognised:
        range: boolean
      reason:
```

- **Match the prompt.** The attribute names are the keys the prompt asks for. peptalk looks for those keys in
  the reply, and an answer needs at least two of them to be found.
- **Keep attributes optional** (no `required: true`). Models leave keys out, and a missing key should not throw
  the answer away. Extra keys a model adds are kept.
- **Reuse the building blocks.** `peptalk_common` provides `AnswerBase`, `PfamDomain`, `CatalyticResidue`,
  `SubstitutedResidue`, `FunctionalResidue`, `GoTerm`, the `YesNoUncertain` enum, and the range slots
  `transmembrane_helices`, `helices`, `strands` and `contacts`.
- **Descriptions are prompts too.** With `--structured` the JSON Schema, descriptions included, goes to the
  model, so keep them short and consistent with `prompt.txt`.

## 4. Generate the Pydantic model and JSON Schema

```bash
pip install 'peptalk-llm[linkml]'          # LinkML is needed only to generate, never at runtime
peptalk templates generate src/peptalk/templates/localization
```

This writes `schema.py`, Pydantic models that import only pydantic, and `Answer.schema.json`, one file per class
marked `answer: true`. Commit both. `peptalk templates check PATH` fails if they are out of date. In this
repository, `just gen-schema` regenerates every template and the interchange formats, and the tests fail on any
difference.

Before a schema is sent as structured output (`--structured`), peptalk prepares it deterministically
(`peptalk.structured`):

- It drops LinkML's metadata, unused definitions, and payload keys the user did not ask for (`--with`).
- **Anthropic** gets every property of a nested object required, which keeps it under Anthropic's limit on
  optional properties, and then the SDK's transform.
- **OpenAI** gets the strict form: every property required, optional ones nullable.
- **Gemini** gets the schema as it is.

A test checks every template's schema, with and without payload keys, against each provider's documented
subset. In a live run every template passed on Claude Haiku 5.5 and Gemini 3.1 flash-lite. With structured
output the whole reply is the answer object. `peptalk tasks --schema localization` prints the prepared schema.

## 5. Write the hooks

`__init__.py` imports the generated model and adds what a schema cannot say:

```python
from peptalk.checks import ranges_check
from peptalk.schema import Check, Feature
from peptalk.templates import Template, read_prompt
from peptalk.templates.localization.schema import Answer     # generated


def checks(a, seq, params=None) -> list[Check]:      # checks against the sequence: never trust coordinates
    signals = [(s.start, s.end) for s in a.targeting_signals or []]   # optional lists may be None
    return [ranges_check(len(seq), signals, "targeting_signal_bounds")]


def control_signal(a) -> str | None:                 # what a shuffled copy should not get
    return f"recognised as {a.protein_name}" if a.recognised else None


def features(a) -> list[Feature]:                    # located features, for GFF3 (Sequence Ontology type names)
    return [Feature(type="transit_peptide", start=s.start, end=s.end) for s in a.targeting_signals or []]


TEMPLATE = Template(
    name="localization",
    prompt=read_prompt(__file__),
    answer_model=Answer,
    summary="Subcellular location, targeting signals with boundaries, transmembrane helices",
    source="new (not tested in fs2f)",
    checks=checks,
    control_signal=control_signal,
    features=features,
    headline=lambda x: ", ".join(x.get("localization") or []),
)
```

The real module maps each signal type to its SO term and has a fuller headline. Only `name`, `prompt` and
`answer_model` are required. Optional list attributes are `None` when the model leaves them out, so write
`a.targeting_signals or []`.

## 6. Register it

Built-in templates are imported in `_load_builtin()` in `src/peptalk/templates/__init__.py`. A template in another
package (a plugin) keeps the same layout: its own `prompt.txt`, `schema.yaml` (which can import `peptalk_common`),
generated `schema.py` and JSON Schema, and `__init__.py`. It registers itself through an entry point:

```toml
[project.entry-points."peptalk.templates"]
localization = "my_package.localization:TEMPLATE"
```

or by calling `peptalk.templates.register(TEMPLATE)` before use.

## 7. Test it

- `peptalk templates check PATH`: the generated files are current.
- Doctests in the module for the checks, features and headline (see `localization/__init__.py`).
- `tests/test_tasks.py::test_every_template_renders_and_has_a_schema` renders every registered template at the
  `organism` level with a payload, and checks that no placeholder is left and that the JSON Schema is an object.
- A dry run calls no model: `peptalk annotate examples/proteins.fasta -t localization --provider stub -m stub`.
- Then a few live questions with a cheap model, and a look at `peptalk log` to see that the input-token check
  passed.

## 8. Versioning

`peptalk tasks` shows each template's version: the first 12 hex digits of the SHA-256 of its prompt file. Any
edit to `prompt.txt` gives a new version. Stored answers are keyed by version, so they are never reused for the
new prompt. Changing only the Python hooks (checks, features) or the schema keeps the version, and stored
answers are re-checked with the new code when reused.

## Ask templates: parameters

An ask template puts one claim to the model and takes a verdict. Declare its parameters, and use them in the
prompt:

```python
Template(
    name="ask-localization",
    prompt=read_prompt(__file__, "localization.txt"),   # "... decide whether this protein is located in the {{compartment}}. ..."
    answer_model=Verdict,                               # generated from ask/schema.yaml: verdict, reason
    params={"compartment": "a cellular compartment, e.g. mitochondrial inner membrane"},
    control_signal=lambda a: "shuffled copy also got 'yes'" if a.verdict == "yes" else None,
)
```

The values come from `--param compartment=nucleus` on `peptalk annotate`, from a claims file on `peptalk ask`,
or from `"params"` in the REST API. They are part of the cache key. A claims file names the template and its
parameters for each claim; see [claims.md](claims.md) and [`examples/claims.yaml`](../examples/claims.yaml).
`ask-catalytic-residue` also shows a check that uses its parameters: it confirms that the claimed residue is
really at the claimed position before anyone reads the verdict.

```bash
peptalk ask examples/proteins.fasta --claims examples/claims.yaml -c blind -w confidence --shuffle-control
```
