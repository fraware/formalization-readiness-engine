# Formalization Readiness Engine: Engineering Implementation Plan

This document is the technical foundation for the Formalization Readiness Engine. The project should be implemented as a reproducible research-engineering system, not as a thin LLM application.

The central idea is to build a compiler-like front end for informal mathematics. Given a theorem/proof unit from LaTeX or author-permitted notes, the system should recover source-grounded structure, identify ambiguity and missing prerequisites, align candidates with mathlib where possible, and emit formalization-ready tasks for Lean.

## 1. Core engineering principle

Build the system around versioned artifacts, not around chat outputs.

Every pipeline stage must produce structured objects that can be inspected, validated, reviewed, scored, exported, and reproduced.

```text
LaTeX / notes
  -> theorem/proof unit extraction
  -> local context and notation recovery
  -> proof-graph evidence
  -> readiness report
  -> mathlib alignment
  -> LeanTask package
  -> Formalization Gap Atlas records
  -> benchmark score
```

The system should answer six questions for every theorem/proof unit.

1. What was recovered from the source text?
2. What remains ambiguous?
3. What maps to existing mathlib definitions or theorems?
4. What theorem may already exist under a different formal name?
5. What missing lemmas, definitions, imports, or typeclass assumptions block formalization?
6. What Lean-facing action should be attempted next?

## 2. Repository architecture

The repository is organized as a monorepo with separate spaces for applications, core packages, Lean tasks, examples, tests, and documentation.

```text
formalization-readiness-engine/
  apps/
    api/                  FastAPI backend after schemas stabilize
    review-ui/            Human review interface after artifact validation
    docs-site/            Public documentation site before release
  packages/
    fre_core/             Python schemas, validators, OpenAI calls, CLI, artifact utilities
  docs/
    IMPLEMENTATION_PLAN.md
    ARCHITECTURE.md
    OPENAI_USAGE.md
  examples/
    finite_tree/          Hand-authored reference artifacts for the first demo
  lean/
    lakefile.lean
    FRETasks/
      Examples/
  tests/
    schema and artifact tests
```

## 3. OpenAI API integration

The project will use the OpenAI API for model calls. All model calls must go through one internal client module.

Do not call the OpenAI API directly from extraction modules, notebooks, tests, scripts, or the review UI.

Centralizing model calls gives the project:

- one place for API keys and environment handling;
- one place for retry logic and rate-limit behavior;
- one place for structured output validation;
- one place for logging prompts, model versions, and schema versions;
- one place for future provider substitution.

Environment variable:

```bash
OPENAI_API_KEY=...
```

The first production model use should be schema-constrained JSON extraction for readiness reports. Free-form text generation should not enter benchmark artifacts.

## 4. Main components

### 4.1 Corpus Manager

The Corpus Manager tracks source documents, licensing, release mode, and domain tags.

Every source document should have a record like this.

```json
{
  "source_id": "graph_theory_notes_001",
  "source_type": "author_permitted_notes",
  "license_status": "permission_granted",
  "release_mode": "full_text_allowed",
  "domain": "graph_theory",
  "path": "data/raw_sources/graph_theory_notes_001.tex"
}
```

No source should enter a public benchmark export unless release permissions are explicit.

### 4.2 Ingestion and Segmentation

The ingestion layer converts LaTeX sources and notes into theorem/proof units.

A theorem/proof unit is the atomic source object of the project. It contains a theorem statement, proof body, local context, source spans, document metadata, and a domain label.

Segmentation should combine deterministic parsing with model-assisted repair only where deterministic parsing fails.

### 4.3 Readiness Extraction

The Readiness Extractor produces structured fields from a theorem/proof unit.

It should recover objects, assumptions, notation, proof strategy, dependencies, hidden assumptions, missing prerequisites, existing-theorem candidates, library blockers, and recommended next actions.

Outputs must validate against the `ReadinessReport` schema.

### 4.4 ProofGraph Builder

The ProofGraph Builder converts readiness extraction into graph evidence.

Nodes should include theorem statements, definitions, objects, assumptions, proof steps, diagrams, constructions, missing prerequisites, library candidates, and LeanTask targets.

Edges should include uses, defines, depends-on, transports, specializes, invokes-universal-property, requires-lemma, and aligns-with-library-theorem.

Every graph must pass deterministic validation before it can become Silver or Gold data.

### 4.5 mathlib Alignment Service

The mathlib Alignment Service indexes Lean/mathlib declarations and supports lexical, namespace, type, import, and embedding search.

It should distinguish candidate alignment from confirmed alignment. A model or retrieval system can propose candidates; Silver and Gold records require human review.

### 4.6 LeanTask Generator

LeanTask packages connect readiness reports to formalization action.

- L0 is a planning package with source span, informal statement, proof-graph evidence, blockers, candidate imports, and next action.
- L1 is a typechecked Lean theorem statement with imports and `sorry` placeholders.
- L2 is an existing-theorem alignment, missing-lemma decomposition, or partial proof skeleton for selected Gold examples.

### 4.7 Formalization Gap Atlas

The Formalization Gap Atlas is a curated map of recurring formalization blockers.

Atlas records should include blocker type, mathematical pattern, evidence span, candidate formal object, likely library location, severity, status, and recommended action.

The Atlas is not a generic error log. It is a public research artifact for prioritizing missing infrastructure between informal mathematics and formal proof.

### 4.8 Review UI

The review UI should support human inspection and correction of source units, readiness reports, proof graphs, Atlas records, and LeanTask packages.

The first version can be simple. It must support high-quality review before interface polish.

## 5. Data tiers

### Bronze

Automatically extracted data.

Bronze artifacts must be schema-valid and source-linked, but they are not guaranteed correct.

### Silver

Human-reviewed data.

Silver artifacts require checked source spans, corrected readiness fields, and fixed obvious graph errors.

### Gold

Expert-reviewed data.

Gold artifacts require mathematical review, library-alignment review, blocker review, severity review, and LeanTask review.

## 6. Deployment strategy

For the first year, deploy as a reproducible research system with a thin web interface.

Recommended local stack:

```text
Docker Compose
  + PostgreSQL
  + object storage or local artifact storage
  + FastAPI backend
  + review UI
  + extraction worker
  + Lean worker
  + evaluation runner
```

Use Redis and RQ, or Celery if the team strongly prefers it, for long-running extraction and Lean jobs. Avoid Kubernetes until the system has real users and stable workloads.

## 7. CI and quality gates

CI must enforce the following gates.

1. All schemas validate.
2. All unit tests pass.
3. Example artifacts remain valid.
4. Generated Lean examples compile where marked L1 or L2.
5. Evaluation metrics reproduce on checked fixtures.
6. Public artifact export works.
7. Documentation builds.
8. Restricted source text does not leak into public exports.

The licensing leak test is part of the public-good commitment. It should be implemented before the first public benchmark export.

## 8. Engineering phases

### Phase 0: Technical foundation

Target duration: 1 to 2 weeks.

Deliverables:

- repository structure;
- Python package scaffold;
- OpenAI client boundary;
- pinned Lean/mathlib environment;
- schema package;
- finite-tree example;
- category-theory example;
- basic CI.

Exit criterion:

```text
make demo
```

produces one theorem/proof unit, one readiness report, one proof graph, one Atlas record, one LeanTask package, and one Lean check attempt.

### Phase 1: Artifact schemas and validation

Target duration: 2 to 4 weeks.

Deliverables:

- `SourceDocument` schema;
- `TheoremProofUnit` schema;
- `ReadinessReport` schema;
- `ProofGraph` schema;
- `AtlasRecord` schema;
- `LeanTaskPackage` schema;
- validators;
- JSON Schema exports;
- example artifacts.

Exit criterion:

All examples validate, and schemas are stable enough for extraction work.

### Phase 2: Ingestion and segmentation

Target duration: 4 to 6 weeks.

Deliverables:

- LaTeX ingestion;
- theorem/proof environment parser;
- source-span preservation;
- document metadata;
- 30 extracted units.

Exit criterion:

Thirty theorem/proof units extracted from three to five sources with source spans.

### Phase 3: Extraction baselines

Target duration: 6 to 8 weeks.

Deliverables:

- direct OpenAI extraction baseline;
- OpenAI plus mathlib retrieval baseline;
- ablated baseline without library-alignment feedback;
- comparison harness;
- first readiness reports.

Exit criterion:

Thirty units produce schema-valid reports and proof graphs, with errors categorized.

### Phase 4: mathlib alignment and LeanTask generation

Target duration: 8 to 10 weeks.

Deliverables:

- mathlib declaration index;
- theorem candidate search;
- import suggestion;
- LeanTask L0;
- initial L1 for aligned units;
- Lean checker integration.

Exit criterion:

The finite-tree example reaches L1 or L2 alignment, and at least ten aligned units produce typechecked theorem statements or confirmed existing-theorem alignment reports.

### Phase 5: Review workflow

Target duration: 8 to 10 weeks.

Deliverables:

- review UI;
- annotation workflow;
- Bronze/Silver/Gold tagging;
- versioned reviewer edits.

Exit criterion:

Reviewers can produce Silver and Gold artifacts through the interface.

### Phase 6: Benchmark and Atlas release

Target duration: 6 to 8 weeks.

Deliverables:

- evaluation runner;
- benchmark score reports;
- Atlas generator;
- public JSONL exports;
- documentation;
- technical report.

Exit criterion:

External users can run the benchmark, inspect examples, and open LeanTask packages without project-team assistance.

## 9. Two-week architecture sprint

The first sprint should establish technical reality before model complexity.

### Days 1 to 2

Create repo structure, Docker stack, Lean/mathlib environment, and CI skeleton.

### Days 3 to 4

Implement Pydantic schemas.

### Days 5 to 6

Create hand-authored artifacts for the finite-tree theorem and pullback transport along equivalence.

### Days 7 to 8

Implement validators and JSONL export.

### Days 9 to 10

Implement a minimal LeanTask runner that writes `.lean` files and runs Lean inside Docker.

### End-of-sprint demo

```text
one source theorem
  -> one extracted theorem/proof unit
  -> one readiness report
  -> one proof graph
  -> one Atlas record
  -> one LeanTask L0
  -> one Lean check attempt
```

## 10. Technical risks and mitigations

### Vague model outputs

Mitigation: constrained JSON schemas, validation, and rejection of incomplete outputs.

### Unreliable mathlib alignment

Mitigation: separate candidate alignment from confirmed alignment, and require reviewer approval for Silver and Gold.

### L1 LeanTask difficulty

Mitigation: L0 for all reviewed units, L1 only for aligned units, L2 only for selected Gold examples.

### Corpus licensing risk

Mitigation: source registry, release modes, and public export filters.

### Reviewer disagreement

Mitigation: annotation guide, inter-annotator checks, uncertainty fields, and Gold review for stable items only.

## 11. System framing

The project is not an LLM app. It is a benchmarked compiler front end for informal mathematics.

Its value depends on artifact discipline: source spans, schemas, validation, reproducibility, Lean checks, review state, public export, and benchmark metrics.
