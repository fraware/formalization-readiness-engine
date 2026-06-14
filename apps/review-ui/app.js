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

const alignmentStatus = document.getElementById("alignment-status");

const alignmentCandidates = document.getElementById("alignment-candidates");

const suggestedImports = document.getElementById("suggested-imports");

const promoteAlignmentButton = document.getElementById("promote-alignment");



let currentReport = null;

let currentUnit = null;

let alignmentResult = null;

let confirmedAlignmentNames = [];

let suggestedImportModules = [];



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



async function postJson(path, payload) {

  const response = await fetch(`${apiBase()}${path}`, {

    method: "POST",

    headers: { "Content-Type": "application/json" },

    body: JSON.stringify(payload),

  });

  const body = await response.json();

  if (!response.ok) {

    throw new Error(JSON.stringify(body.detail || body));

  }

  return body;

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

    confirmed_alignment_full_names: [],

    suggested_import_modules: [],

    notes: "Local review UI submission.",

  };

}



function syncReviewJson() {

  if (!currentReport) {

    return;

  }

  const submission = defaultReviewTemplate(currentReport);

  submission.confirmed_alignment_full_names = [...confirmedAlignmentNames];

  submission.suggested_import_modules = [...suggestedImportModules];

  reviewJson.value = JSON.stringify(submission, null, 2);

}



function renderAlignmentCandidates() {

  if (!alignmentResult || !alignmentResult.candidates.length) {

    alignmentCandidates.innerHTML = "<p>No alignment candidates returned.</p>";

    promoteAlignmentButton.disabled = true;

    return;

  }



  alignmentCandidates.innerHTML = alignmentResult.candidates

    .map((candidate) => {

      const checked = confirmedAlignmentNames.includes(candidate.full_name) ? "checked" : "";

      return `

        <label class="alignment-row">

          <input type="checkbox" class="alignment-confirm" data-full-name="${candidate.full_name}" ${checked} />

          <span class="alignment-name">${candidate.full_name}</span>

          <span class="alignment-meta">score=${candidate.score}, module=${candidate.module}</span>

        </label>

      `;

    })

    .join("");



  alignmentCandidates.querySelectorAll(".alignment-confirm").forEach((box) => {

    box.addEventListener("change", () => {

      const name = box.dataset.fullName;

      if (box.checked && !confirmedAlignmentNames.includes(name)) {

        confirmedAlignmentNames.push(name);

      }

      if (!box.checked) {

        confirmedAlignmentNames = confirmedAlignmentNames.filter((entry) => entry !== name);

      }

      promoteAlignmentButton.disabled = confirmedAlignmentNames.length === 0;

      syncReviewJson();

    });

  });



  promoteAlignmentButton.disabled = confirmedAlignmentNames.length === 0;

}



function renderSuggestedImports() {

  suggestedImports.textContent = suggestedImportModules.length

    ? suggestedImportModules.join("\n")

    : "(none promoted yet)";

}



async function loadAlignment() {

  if (!currentReport || !currentUnit) {

    return;

  }

  alignmentResult = await postJson("/align/readiness-report", {

    report: currentReport,

    unit: currentUnit,

    confirmed_full_names: confirmedAlignmentNames,

  });

  alignmentStatus.textContent = `Loaded ${alignmentResult.candidates.length} candidates.`;

  renderAlignmentCandidates();

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

    confirmedAlignmentNames = [];

    suggestedImportModules = [];

    renderReportSummary(currentReport);

    reportJson.textContent = JSON.stringify(currentReport, null, 2);

    await loadAlignment();

    renderSuggestedImports();

    syncReviewJson();

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

promoteAlignmentButton.addEventListener("click", async () => {

  if (!currentReport || !currentUnit) {

    validationResult.textContent = "Load an example first.";

    return;

  }

  try {

    const body = await postJson("/review/promote-alignment", {

      report: currentReport,

      unit: currentUnit,

      confirmed_full_names: confirmedAlignmentNames,

    });

    alignmentResult = body.alignment;

    confirmedAlignmentNames = body.confirmed_alignment_full_names;

    suggestedImportModules = body.suggested_import_modules;

    renderAlignmentCandidates();

    renderSuggestedImports();

    syncReviewJson();

    validationResult.textContent = JSON.stringify(body, null, 2);

  } catch (error) {

    validationResult.textContent = String(error);

  }

});



loadExample();

