import json

from fre_core.schema_exports import SCHEMA_MODELS, export_json_schemas


def test_export_json_schemas_writes_all_public_contracts(tmp_path) -> None:
    written = export_json_schemas(tmp_path)

    assert len(written) == len(SCHEMA_MODELS)
    for path in written:
        assert path.exists()
        payload = json.loads(path.read_text())
        assert payload["type"] == "object"
        assert "properties" in payload
