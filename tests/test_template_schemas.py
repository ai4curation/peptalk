"""Template answer schemas: generated from LinkML, current, pydantic-only, and accepted by every provider."""

import ast
from pathlib import Path

import pytest
from typer.testing import CliRunner

from peptalk.cli import app
from peptalk.structured import anthropic_problems, gemini_problems, openai_strict, openai_strict_problems
from peptalk.templates import TEMPLATES

TEMPLATE_DIR = Path(__file__).parent.parent / "src" / "peptalk" / "templates"
SCHEMAS = sorted(TEMPLATE_DIR.glob("*/schema.yaml"))


def test_every_template_has_a_linkml_schema():
    folders = {Path(__import__(t.answer_model.__module__, fromlist=["x"]).__file__).parent for t in TEMPLATES.values()}
    assert folders == {s.parent for s in SCHEMAS}


@pytest.mark.parametrize("schema", SCHEMAS, ids=lambda p: p.parent.name)
def test_generated_files_are_current(schema):
    pytest.importorskip("linkml", reason="linkml is a development dependency")
    from peptalk.codegen import stale

    assert stale(schema) == [], "run `just gen-schema`"


@pytest.mark.parametrize("schema", SCHEMAS, ids=lambda p: p.parent.name)
def test_generated_models_need_only_pydantic(schema):
    tree = ast.parse((schema.parent / "schema.py").read_text())
    imported = {
        (node.module if isinstance(node, ast.ImportFrom) else alias.name).split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    assert imported <= {"__future__", "re", "sys", "datetime", "decimal", "enum", "typing", "pydantic"}, imported


@pytest.mark.parametrize("name", sorted(TEMPLATES))
def test_schema_fits_every_provider(name):
    schema = TEMPLATES[name].json_schema()
    assert schema["type"] == "object" and "metamodel_version" not in schema
    assert anthropic_problems(schema) == []
    assert openai_strict_problems(schema) == []
    assert gemini_problems(schema) == []


@pytest.mark.parametrize("name", sorted(TEMPLATES))
def test_schema_matches_the_answer_model(name):
    """The JSON Schema and the Pydantic model come from the same LinkML class: same top-level fields."""
    t = TEMPLATES[name]
    assert set(t.json_schema()["properties"]) == set(t.answer_model.model_fields)


def test_openai_strict_keeps_types_and_marks_optional_fields_nullable():
    schema = openai_strict(TEMPLATES["active-site"].json_schema())
    assert schema["properties"]["catalytically_active"]["anyOf"][1] == {"type": "null"}
    assert set(schema["required"]) == set(schema["properties"])


def test_cli_check_and_generate(tmp_path):
    pytest.importorskip("linkml", reason="linkml is a development dependency")
    runner = CliRunner()
    result = runner.invoke(app, ["templates", "check", *map(str, SCHEMAS)])
    assert result.exit_code == 0, result.output
    # a plugin's template, in its own folder, importing the shared building blocks
    plugin = tmp_path / "mytemplate"
    plugin.mkdir()
    (plugin / "schema.yaml").write_text(
        "id: https://example.org/mytemplate\nname: mytemplate\nprefixes:\n  linkml: https://w3id.org/linkml/\n"
        "default_range: string\nimports:\n  - linkml:types\n  - peptalk_common\nclasses:\n  Answer:\n"
        "    is_a: AnswerBase\n    annotations:\n      answer: true\n    attributes:\n      disorder:\n"
        "        range: boolean\n      reason:\n"
    )
    assert runner.invoke(app, ["templates", "check", str(plugin)]).exit_code == 1
    result = runner.invoke(app, ["templates", "generate", str(plugin)])
    assert result.exit_code == 0, result.output
    assert {p.name for p in plugin.iterdir()} == {"schema.yaml", "schema.py", "Answer.schema.json"}
    assert "class Answer(AnswerBase)" in (plugin / "schema.py").read_text()
    assert runner.invoke(app, ["templates", "check", str(plugin)]).exit_code == 0
