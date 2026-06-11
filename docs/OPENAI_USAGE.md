# OpenAI Usage

This document describes how the Formalization Readiness Engine calls OpenAI models. All model access must stay behind the internal structured model-client boundary.

## Environment

Set an API key before running live extraction:

```bash
export OPENAI_API_KEY=...
```

Optional model override:

```bash
export FRE_MODEL_NAME=gpt-4.1
```

Install model dependencies once:

```bash
make setup-models
```

## Architecture rule

Do not import the OpenAI SDK from extraction modules, tests, scripts, notebooks, or the review UI. Provider code lives in `packages/fre_core/src/fre_core/openai_responses_provider.py`. Extraction orchestration depends on the `StructuredModelClient` protocol in `model_client.py`.

## Supported extraction commands

| Command | Input | Output schema |
|---------|-------|---------------|
| `extract-report` | `TheoremProofUnit` JSON | `ReadinessReport` |
| `extract-proofgraph` | `TheoremProofUnit` JSON | `ProofGraph` |
| `extract-atlas` | `TheoremProofUnit` JSON | `AtlasRecord` |
| `generate-leantask` | `TheoremProofUnit` + `ReadinessReport` JSON | `LeanTaskPackage` |

Each command:

1. loads and validates the input unit;
2. builds a source-grounded prompt;
3. calls the provider for schema-constrained JSON;
4. aligns `unit_id` with the source unit when the model drifts;
5. runs semantic validation before writing output.

For `generate-leantask`, the command also accepts an optional `--level` (`L0` or `L1`) and `--enrich-imports` to append mathlib module paths from the declaration index.

## Finite-tree examples

```bash
make extract-finite-tree-proofgraph
make extract-finite-tree-atlas
make generate-finite-tree-leantask
```

Candidate outputs are written under `artifacts/generated/finite_tree/`. That directory is gitignored. Reviewed gold artifacts remain under `examples/finite_tree/`.

## Testing without API access

Unit tests use fake model clients that implement `StructuredModelClient`. They cover prompt construction, `unit_id` alignment, and post-extraction semantic validation, including negative cases for broken proof-graph edges, missing Atlas evidence, and L1 LeanTasks without formal targets.

Run:

```bash
make test
```

## Candidate vs reviewed data

Model outputs are candidate artifacts until they pass schema validation, semantic validation, and human review. Do not copy generated files into benchmark gold directories without an explicit review workflow.
