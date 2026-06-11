from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from fre_core.validation import load_readiness_report

ROOT = Path(__file__).resolve().parents[1]
FINITE_TREE_REPORT = ROOT / "examples" / "finite_tree" / "readiness_report.json"
REVIEW_TEMPLATE = ROOT / "docs" / "review" / "templates" / "readiness_report_review.json"
FINITE_TREE_INDEX = ROOT / "fixtures" / "mathlib_declarations" / "finite_tree_v0.json"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_examples(client: TestClient) -> None:
    response = client.get("/examples")
    assert response.status_code == 200
    names = response.json()
    assert "finite_tree" in names
    assert "category_theory_pullback" in names


def test_get_example_metadata(client: TestClient) -> None:
    response = client.get("/examples/finite_tree")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "finite_tree"
    assert "readiness_report" in payload["artifacts"]


def test_validate_readiness_report(client: TestClient) -> None:
    report = load_readiness_report(FINITE_TREE_REPORT)
    response = client.post("/validate/readiness-report", json=report.model_dump(mode="json"))
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["unit_id"] == report.unit_id


def test_validate_review_submission(client: TestClient) -> None:
    submission = REVIEW_TEMPLATE.read_text(encoding="utf-8")
    response = client.post(
        "/validate/review-submission",
        content=submission,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True


def test_align_readiness_report(client: TestClient) -> None:
    report = load_readiness_report(FINITE_TREE_REPORT)
    response = client.post(
        "/align/readiness-report",
        json={
            "report": report.model_dump(mode="json"),
            "index_path": FINITE_TREE_INDEX.relative_to(ROOT).as_posix(),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["unit_id"] == report.unit_id
    assert body["candidates"]
    assert body["confirmed"] == []
    assert body["candidates"][0]["full_name"] == "SimpleGraph.IsTree.card_edgeFinset"
