const exampleSelect = document.getElementById("example-select");
const loadButton = document.getElementById("load-example");
const loadStatus = document.getElementById("load-status");
const reportSummary = document.getElementById("report-summary");
const reportJson = document.getElementById("report-json");
const reviewJson = document.getElementById("review-json");
const apiBaseInput = document.getElementById("api-base");
const validateReviewButton = document.getElementById("validate-review");
const validateReportButton = document.getElementById("validate-report");
const validationResult = document.getElementById("validation-result");

let currentReport = null;
let currentUnit = null;

function apiBase() {
  return apiBaseInput.value.replace(/\/$/, "");
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
}

function renderReportSummary(report) {
  const blockers = report.blockers?.length ? report.blockers.join("; ") : "(none)";
  const candidates = report.existing_theorem_candidates?.join(", ") || "(none)";
  reportSummary.innerHTML = `
    <dl>
      <dt>Unit</dt><dd>${report.unit_id}</dd>
      <dt>Next action</dt><dd>${report.recommended_next_action}</dd>
      <dt>Blockers</dt><dd>${blockers}</dd>
      <dt>Theorem candidates</dt><dd>${candidates}</dd>
      <dt>Statement status</dt><dd>${report.statement_readiness.status}</dd>
      <dt>Context status</dt><dd>${report.context_readiness.status}</dd>
    </dl>
  `;
}

function defaultReviewTemplate(report) {
  return {
    schema_version: "0.1",
    unit_id: report.unit_id,
    item_id: null,
    reviewer_id: "reviewer.local",
    review_date: new Date().toISOString().slice(0, 10),
    tier_promotion: null,
    review_status: "human_reviewed",
    rubric_scores: {
      source_fidelity: 4,
      actionability: 4,
      library_alignment: 4,
      blocker_specificity: 4,
      path_clarity: 4,
    },
    dimension_reviews: {
      statement_readiness: {
        status_accurate: true,
        recovered_accurate: true,
        unresolved_accurate: true,
        notes: null,
      },
      context_readiness: {
        status_accurate: true,
        recovered_accurate: true,
        unresolved_accurate: true,
        notes: null,
      },
      notation_readiness: {
        status_accurate: true,
        recovered_accurate: true,
        unresolved_accurate: true,
        notes: null,
      },
      dependency_readiness: {
        status_accurate: true,
        recovered_accurate: true,
        unresolved_accurate: true,
        notes: null,
      },
    },
    list_fields_accurate: true,
    recommended_next_action_accurate: true,
    corrected_report_path: null,
    corrected_report: null,
    notes: "Local review UI submission.",
  };
}

async function loadExample() {
  const name = exampleSelect.value;
  loadStatus.textContent = "Loading...";
  validationResult.textContent = "";

  try {
    const metadata = await fetchJson(`${apiBase()}/examples/${name}`);
    const reportPath = `../../${metadata.artifacts.readiness_report}`;
    const unitPath = `../../${metadata.artifacts.unit}`;
    currentReport = await fetchJson(reportPath);
    currentUnit = await fetchJson(unitPath);
    renderReportSummary(currentReport);
    reportJson.textContent = JSON.stringify(currentReport, null, 2);
    reviewJson.value = JSON.stringify(defaultReviewTemplate(currentReport), null, 2);
    loadStatus.textContent = `Loaded ${name} from committed example artifacts.`;
  } catch (error) {
    loadStatus.textContent = String(error);
  }
}

async function postValidation(path, payload) {
  const response = await fetch(`${apiBase()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  validationResult.textContent = JSON.stringify(body, null, 2);
}

loadButton.addEventListener("click", loadExample);
validateReviewButton.addEventListener("click", async () => {
  try {
    const submission = JSON.parse(reviewJson.value);
    await postValidation("/validate/review-submission", submission);
  } catch (error) {
    validationResult.textContent = String(error);
  }
});
validateReportButton.addEventListener("click", async () => {
  if (!currentReport) {
    validationResult.textContent = "Load an example readiness report first.";
    return;
  }
  await postValidation("/validate/readiness-report", currentReport);
});

loadExample();
