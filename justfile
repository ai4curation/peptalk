# Recipes for development. `just` with no arguments lists them.
default:
    @just --list

# Run the tests and doctests
test:
    uv run pytest

# Run only the doctests
doctest:
    uv run pytest src

# Lint and format check
lint:
    uv run ruff check src tests
    uv run ruff format --check src tests

# Type check
mypy:
    uv run mypy src

# Everything CI runs
check: lint mypy test

# Build the sdist and wheel into dist/ (does not publish)
build:
    rm -rf dist
    uv build

# One live call per task on the example file with a cheap model (about one cent; needs ANTHROPIC_API_KEY; logged in the default store)
smoke model="claude-haiku-5-5":
    uv run peptalk annotate examples/proteins.fasta -m {{model}} -e low -t features -t active-site --no-reuse -f tsv

# Regenerate everything generated from LinkML: the interchange formats (src/peptalk/datamodel) and each template's answer schema
gen-schema:
    uv run gen-pydantic --meta None src/peptalk/datamodel/peptalk.yaml > src/peptalk/datamodel/peptalk.py
    uv run gen-json-schema --top-class ClaimsFile src/peptalk/datamodel/peptalk.yaml > src/peptalk/datamodel/claims.schema.json
    uv run gen-json-schema --top-class Annotation src/peptalk/datamodel/peptalk.yaml > src/peptalk/datamodel/annotation.schema.json
    rm -rf docs/schema && uv run gen-doc --subfolder-type-separation --directory docs/schema src/peptalk/datamodel/peptalk.yaml
    uv run peptalk templates generate src/peptalk/templates/*/schema.yaml

# Fail if the committed generated files differ from what the LinkML sources generate
check-schema:
    uv run pytest -q tests/test_datamodel.py tests/test_template_schemas.py
