"""The interchange schemas: LinkML is the source of truth, and the committed generated files must match it."""

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from peptalk import schema
from peptalk.annotator import Annotator
from peptalk.claims import _Yaml12Loader
from peptalk.datamodel import peptalk as datamodel
from peptalk.fasta import read_fasta
from peptalk.providers import get_provider
from peptalk.templates import CONTEXTS

ROOT = Path(__file__).parent.parent
DATAMODEL = ROOT / "src" / "peptalk" / "datamodel"
SOURCE = DATAMODEL / "peptalk.yaml"


def generate(tool: str, *args: str) -> str:
    exe = Path(sys.executable).parent / tool
    return subprocess.run([str(exe), *args, str(SOURCE)], check=True, capture_output=True, text=True).stdout


@pytest.fixture(scope="module")
def linkml():
    return pytest.importorskip("linkml", reason="linkml is a development dependency (uv sync --group dev)")


def test_pydantic_is_current(linkml):
    assert generate("gen-pydantic", "--meta", "None") == (DATAMODEL / "peptalk.py").read_text(), "run `just gen-schema`"


@pytest.mark.parametrize("top,name", [("ClaimsFile", "claims.schema.json"), ("Annotation", "annotation.schema.json")])
def test_json_schema_is_current(linkml, top, name):
    assert generate("gen-json-schema", "--top-class", top) == (DATAMODEL / name).read_text(), "run `just gen-schema`"


def test_docs_are_current(linkml, tmp_path):
    subprocess.run(
        [
            str(Path(sys.executable).parent / "gen-doc"),
            "--subfolder-type-separation",
            "--directory",
            str(tmp_path),
            str(SOURCE),
        ],
        check=True,
        capture_output=True,
    )
    committed = ROOT / "docs" / "schema"

    def files(root: Path) -> list[str]:
        return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())

    assert files(tmp_path) == files(committed), "run `just gen-schema`"
    for name in files(tmp_path):
        assert (tmp_path / name).read_text() == (committed / name).read_text(), (
            f"docs/schema/{name}: run `just gen-schema`"
        )


def test_generated_module_needs_only_pydantic():
    tree = ast.parse((DATAMODEL / "peptalk.py").read_text())
    imported = {
        (node.module if isinstance(node, ast.ImportFrom) else alias.name).split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported <= {"__future__", "re", "sys", "datetime", "decimal", "enum", "typing", "pydantic"}, imported


def test_runtime_record_adds_no_fields():
    assert set(schema.Annotation.model_fields) == set(datamodel.Annotation.model_fields)


def test_enums_match_the_code():
    assert {e.value for e in datamodel.HeaderContext} == set(CONTEXTS)
    assert {e.value for e in datamodel.Confidence} == set(schema.Confidence.__args__)
    assert {e.value for e in datamodel.Verdict} == {"yes", "no", "uncertain"}


def test_examples_validate_against_the_json_schemas():
    jsonschema = pytest.importorskip("jsonschema")
    claims_schema = json.loads((DATAMODEL / "claims.schema.json").read_text())
    example = yaml.load((ROOT / "examples" / "claims.yaml").read_text(), Loader=_Yaml12Loader)
    jsonschema.validate(example, claims_schema)
    record = Annotator(get_provider("stub"), "stub").annotate(
        read_fasta(ROOT / "examples" / "proteins.fasta"), ["features"]
    )[0]
    annotation_schema = json.loads((DATAMODEL / "annotation.schema.json").read_text())
    jsonschema.validate(json.loads(record.model_dump_json()), annotation_schema)
