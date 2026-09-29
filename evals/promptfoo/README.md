# VendorLens Promptfoo evaluation

This evaluation exercises the running VendorLens API, not a separate copy of
the prompts or a direct Azure OpenAI client. It therefore measures the actual
redaction boundary, ChromaDB retrieval, grounded answer prompt, citations,
global assistant prompt, API latency, and token counts.

## Prerequisites

- Node.js 20 or newer and npm/npx.
- The FastAPI backend running on `http://localhost:8000`.
- The existing processed **Kaveri Flow Controls Private Limited** fixture, or a
  supplier with its same legacy document facts, for the reviewer RAG cases.
- AI-provider credentials for the two generative suites.

The default RAG cases use **Kaveri Flow Controls Private Limited** because its
expected values are already versioned in
`sample_documents/evaluation_sets/evaluation_manifest.json`. To evaluate a
different supplier, replace `supplier_name` and expected values in
`promptfooconfig.yaml`, or set `PROMPTFOO_SUPPLIER_ID` and remove the
`supplier_name` values from the RAG cases.

## Authentication and test data

The provider creates a reviewer-demo session automatically for protected RAG
routes. No reviewer credential is required locally; set
`PROMPTFOO_REVIEWER_TOKEN` to use another reviewer session.

The signed-in application-assistant cases create or log in to the local
`promptfoo.cybersecurity@example.com` account and save an unsubmitted
Cybersecurity (`TECH-CYB`) draft. They do not upload evidence or submit it.
Automatic setup is refused for non-local URLs. For remote evaluation, set
`PROMPTFOO_SUPPLIER_TOKEN`, or `PROMPTFOO_SUPPLIER_EMAIL` and
`PROMPTFOO_SUPPLIER_PASSWORD`.

Set `PROMPTFOO_BASE_URL` to change the API address. `PROMPTFOO_SUPPLIER_ID`
can select a different processed supplier for the legacy RAG tests.


## Run locally without admin access

From this directory, use `npx`; it downloads Promptfoo to the npm cache and
does not require a global installation:

```powershell
$env:PROMPTFOO_BASE_URL = "http://localhost:8000"
npx promptfoo@0.123.1 eval -c promptfooconfig.yaml --no-cache -o results/latest.json
```

For a specific supplier ID:

```powershell
$env:PROMPTFOO_SUPPLIER_ID = "<processed-supplier-uuid>"
npx promptfoo@0.123.1 eval -c promptfooconfig.yaml --no-cache -o results/latest.json
```

The first run may download the pinned Promptfoo package. Use
`npx promptfoo@0.123.1 view` to open the local results viewer after an evaluation,
or inspect the JSON report under `evals/promptfoo/results/`.

## What is checked

### Supplier-scoped RAG

- JSON response contract and `information_found` flag.
- Expected answer terms for legal name, payment terms, and insurance expiry.
- At least one citation from an expected document for answerable questions.
- Exact guarded not-found behavior with zero citations for absent data.
- No terms from the other evaluation suppliers in the active supplier answer.
- RAG latency under the five-second demo target.

### Global onboarding assistant

- Category-specific evidence is explained instead of a universal three-file list.
- The assistant explains process, human review, compliance, and approval flow.
- Sensitive credential and bank-value requests are refused without disclosure.
- Supplier-specific questions are redirected to the cited document Q&A panel.
- Assistant latency under the five-second demo target.

### Signed-in application assistant

- The selected Cybersecurity checklist contains three baseline items plus
  confidentiality, security, privacy, continuity, and cyber-liability evidence.
- A draft account accurately reports all eight items as outstanding.
- A draft is not presented as submitted, processed, or review-complete.

These portal cases are deterministic and do not invoke the model. The global
assistant and RAG cases continue to exercise the deployed AI path.



## Interpreting the score

Every assertion returns component scores in Promptfoo. A test passes only when
all of its deterministic checks pass. A failed case is useful evidence: open
the JSON result, inspect the returned answer/citations, and decide whether the
problem is retrieval, grounding, prompt wording, or an expected-value issue.

This is a deterministic regression suite, not a guarantee of production
quality. Add paraphrases, missing fields, expired policies, conflicting
documents, and multi-page/scanned PDFs as the evaluation corpus grows. If a
model-graded check is added later, label it probabilistic and keep these
programmatic checks as the deployment gate.

## Files

- `promptfooconfig.yaml` — providers, prompts, and twelve regression cases.
- `api_provider.py` — shared HTTP provider and token/latency metadata mapping.
- `rag_provider.py` — supplier-scoped `/questions` provider entry point.
- `assistant_provider.py` — global `/assistant/chat` provider entry point.
- `application_assistant_provider.py` — signed-in `/portal/application/assistant` entry point.
- `assertions.py` — deterministic JSON, citation, isolation, boundary, and
  latency assertions.
- `results/` — ignored local Promptfoo output.
