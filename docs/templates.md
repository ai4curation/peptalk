# Writing a template

A template is what one task asks, what the answer must look like, and how peptalk checks it. This page walks
through the `localization` template that ships with peptalk, from an empty directory to a tested task. The
design is in [design.md](design.md#4-templates).

## 1. Make the directory

```
src/peptalk/templates/localization/
    __init__.py
    prompt.txt
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

## 3. Write the answer model and hooks

```python
from pydantic import Field

from peptalk.checks import ranges_check
from peptalk.schema import AnswerModel, Check, Feature, Range
from peptalk.templates import Template, read_prompt


class TargetingSignal(AnswerModel):
    type: str | None = None
    start: int | None = None
    end: int | None = None


class Answer(AnswerModel):          # AnswerModel: extra keys kept, every field optional, payload fields included
    localization: list[str] = Field(default_factory=list)
    targeting_signals: list[TargetingSignal] = Field(default_factory=list)
    transmembrane_helices: list[Range] = Field(default_factory=list)
    protein_name: str | None = None
    recognised: bool | None = None
    reason: str | None = None


def checks(a, seq, params=None) -> list[Check]:      # checks against the sequence: never trust coordinates
    return [ranges_check(len(seq), [(s.start, s.end) for s in a.targeting_signals], "targeting_signal_bounds")]


def control_signal(a) -> str | None:                 # what a shuffled copy should not get
    return f"recognised as {a.protein_name}" if a.recognised else None


def features(a) -> list[Feature]:                    # located features, for GFF3 (Sequence Ontology type names)
    return [Feature(type="transit_peptide", start=s.start, end=s.end) for s in a.targeting_signals]


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
`answer_model` are required. The field names of the answer model are the keys peptalk looks for in the reply,
and an answer needs at least two of them to be found. Keep fields optional: models leave keys out, and a missing
key should not throw the answer away.

## 4. Register it

Built-in templates are imported in `_load_builtin()` in `src/peptalk/templates/__init__.py`. A template in another
package registers itself through an entry point:

```toml
[project.entry-points."peptalk.templates"]
localization = "my_package.localization:TEMPLATE"
```

or by calling `peptalk.templates.register(TEMPLATE)` before use.

## 5. Test it

- Doctests in the module for the checks, features and headline (see `localization/__init__.py`).
- `tests/test_tasks.py::test_every_template_renders_and_has_a_schema` renders every registered template at the
  `organism` level with a payload, and checks that no placeholder is left and that the JSON Schema is an object.
- A dry run calls no model: `peptalk annotate examples/proteins.fasta -t localization --provider stub -m stub`.
- Then a few live questions with a cheap model, and a look at `peptalk log` to see that the input-token check
  passed.

## 6. Versioning

`peptalk tasks` shows each template's version: the first 12 hex digits of the SHA-256 of its prompt file. Any
edit to `prompt.txt` gives a new version. Stored answers are keyed by version, so they are never reused for the
new prompt. Changing only the Python hooks (checks, features) keeps the version, and stored answers are
re-checked with the new code when reused.

## Ask templates: parameters

An ask template puts one claim to the model and takes a verdict. Declare its parameters, and use them in the
prompt:

```python
Template(
    name="ask-localization",
    prompt=read_prompt(__file__, "localization.txt"),   # "... decide whether this protein is located in the {{compartment}}. ..."
    answer_model=Verdict,                               # verdict: "yes" | "no" | "uncertain"; reason
    params={"compartment": "a cellular compartment, e.g. mitochondrial inner membrane"},
    control_signal=lambda a: "shuffled copy also got 'yes'" if a.verdict == "yes" else None,
)
```

The values come from `--param compartment=nucleus` on `peptalk annotate`, from a claims file on `peptalk ask`
(one row per claim: `id`, `task`, then one column per parameter), or from `"params"` in the REST API. They are
part of the cache key. `ask-catalytic-residue` also shows a check that uses its parameters: it confirms that the
claimed residue is really at the claimed position before anyone reads the verdict.

```text
id	task	term	label	position	residue
Q2PAY3_wt	ask-catalytic-residue			436	D
Q2PAY3_wt	ask-function	GO:0004672	protein kinase activity
```

```bash
peptalk ask examples/proteins.fasta --claims claims.tsv -c blind -w confidence --shuffle-control
```
