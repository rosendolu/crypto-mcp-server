---
name: create-new-requirement
description: Creates an iterative, implementable requirement document for the Crypto MCP Server by mapping requested features to `ccxt` exchange capabilities and the repo’s existing MCP tools/providers. Use when the user asks to add new functionality, expand exchange support, or upgrade the technical approach (framework/model/API), and the agent should then implement via `develop-skill`.
---

# Create New Requirement

## Instructions
This skill turns a user request into a developable change plan, based on:
- `ccxt` exchange capability differences (methods available per exchange)
- This repo’s existing implemented tool surface in `docs/tool-prompts.md`
- Current CCXT provider capabilities in `src/data-providers/ccxt/index.ts`
- Existing indicator/analysis capabilities in `src/indicators/*` and `src/api/tools/index.ts`

### Phase 1: Discovery, Mapping, and V1 Deliverable
1. Parse the user request and classify it into one or more categories (market data, order execution, account info, indicators/analysis, logs/diagnostics, or technical/framework upgrades).
2. Identify what already exists:
   - List the closest matching tools/functions from `docs/tool-prompts.md`.
   - For CCXT-backed capabilities, map to the functions already implemented in `src/data-providers/ccxt/index.ts`.
3. Map the new need to `ccxt` methods:
   - Prefer to implement the change by calling an appropriate `ccxt` exchange method (or existing CCXT functionality already used by this repo).
   - If an exchange method might not be present on all exchanges, mark it as “exchange-dependent” and select a minimal exchange set for testing.
4. Choose a recommended “best” approach if requirements are ambiguous:
   - Default to the safest incremental V1 scope that can be shipped and tested with existing patterns.
   - When multiple implementation options exist, prefer the one that minimizes API/tool changes and maximizes reuse of existing provider functions.
5. Produce a V1 deliverable definition:
   - What the user can do after V1
   - What exchanges are targeted for V1 testing
   - What is explicitly out-of-scope for V1

### Phase 2: Write the Iterative Requirement Doc (under `docs/`)
1. Create a new doc under `docs/requirements/` (create the folder if missing).
2. Use a filename like: `docs/requirements/<short-slug>-req-v1.md`.
3. Generate a short slug from the user request (letters/numbers/hyphens only; no spaces).
4. The doc MUST include the following sections:
   - `Title`
   - `Status` (set to `ready-for-dev`)
   - `Summary` (3-6 sentences)
   - `Motivation` (why this is useful)
   - `User story` (who uses it and what they gain)
   - `Scope`
     - `In scope`
     - `Out of scope`
   - `CCXT capability mapping`
     - `Requested feature`
     - `Needed ccxt methods/endpoints (by name)`
     - `Exchange dependency notes` (what may not exist for every exchange)
     - `V1 test exchanges` (pick a minimal set; if uncertain, use `binance` + one other from `docs/README.zh-CN.md`)
   - `Repo integration plan`
     - Which existing provider functions/tools will be extended or added
     - Any required TypeScript type/module changes (respecting the repo conventions)
   - `API / Tool changes (if any)`
     - Describe MCP tool schema changes to `src/api/tools/index.ts` (parameters, defaults, validation)
   - `Error handling & logging expectations`
     - Must use the repo logger via the existing winston helper (no `console.log`)
     - Must handle missing/exchange-dependent capabilities gracefully
   - `Acceptance criteria`
     - List concrete pass/fail checks for V1
   - `Milestones`
     - `V1` (ship)
     - `V2+` (follow-ups, if applicable)
   - `Test plan`
     - Unit tests (if applicable)
     - Integration/manual test steps

### Phase 3: Confirm Requirement (No extra user questions)
1. Treat the generated V1 deliverable as confirmed by default.
2. If any detail is missing, apply the recommended best option immediately and record the assumption in the requirement doc under `Scope` or `Assumptions`.
3. Re-check that the doc:
   - is exchange-aware for `ccxt`
   - targets a minimal shippable V1
   - matches the existing tool/provider design style in this repo

### Phase 4: Implement via `develop-skill`
After the requirement doc is written and marked `ready-for-dev`, the agent MUST execute the implementation phase by following `develop-skill` exactly:
1. Use the feature description from the requirement doc as the input for the development change.
2. Follow the branching + single-PR + `code-review` loop described in `develop-skill`.
3. Keep the PR scope aligned with the V1 deliverable only.

## Example
Input (user request): “Add funding rate support for futures exchanges and expose it as a new MCP tool/indicator.”

Expected behavior:
- Create `docs/requirements/funding-rate-futures-req-v1.md`
- Document `ccxt` method mapping (exchange-dependent)
- Choose `binance` + one additional exchange from the supported list as V1 test exchanges
- Mark `Status: ready-for-dev`
- Then implement the V1 using `develop-skill`

