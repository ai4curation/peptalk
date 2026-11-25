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
    uv run lpa annotate tests/data/example.fasta -m {{model}} -e low -t features -t active-site --no-reuse -f tsv
