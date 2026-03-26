---
name: code-review
description: >
    Perform structured, severity-graded code reviews on changed/diff code. Use this skill whenever
    the user submits a code diff, patch, pull request snippet, or says "review my code", "check this
    change", "LGTM?", "can you review", "code review", or pastes before/after code blocks. Also trigger
    when the user asks about potential bugs, security issues, or data compatibility problems in code.
    Always apply this skill even for small snippets — every change deserves a graded review.
---

# Code Review Skill

A structured skill for reviewing code changes with severity grading, impact scoping, and data compatibility analysis.

---

## Review Output Format

Every review MUST follow this exact structure:

### 1. Summary Header

```
## Code Review — [filename or feature description]
Reviewed: [N] issues — 🔴 Critical: X  |  🟡 Major: Y  |  🔵 Minor: Z
```

### 2. Issue Blocks (one per finding)

```
### [SEVERITY EMOJI] [SEVERITY LABEL] — [Short Issue Title]

**Location**: [file:line or function name or code excerpt]
**Impact Scope**: [Line / Function / Module / Service / System-wide]
**Potential Impact**: [What can go wrong — bugs, data loss, security breach, UX breakage, etc.]

**Problem**:
[Clear explanation of the defect. Reference the actual code.]

**Fix / Recommendation**:
[Concrete code suggestion or remediation steps]

---
```

### 3. Data Compatibility Section (mandatory)

Always include a dedicated section at the end:

```
## 🔄 Data Compatibility Analysis

[Findings on type coercion, null/undefined handling, encoding issues, locale-sensitive comparisons,
user-supplied input edge cases, schema migrations, backward compatibility, etc.]

If no issues found, still confirm: "✅ No data compatibility issues detected."
```

### 4. Overall Verdict

```
## Verdict
[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]
[1–3 sentence summary of the overall state of the diff and recommended next steps]
```

---

## Severity Definitions

| Level       | Emoji | Label        | When to Use                                                                                                                                                           |
| ----------- | ----- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 — Highest | 🔴    | **Critical** | Data loss, security vulnerabilities (injection, auth bypass, exposure of PII), crashes in production, breaking API contracts, silent data corruption                  |
| 2 — Medium  | 🟡    | **Major**    | Logic errors that produce wrong results under realistic inputs, race conditions, missing error handling on important paths, performance cliffs, incorrect comparisons |
| 3 — Lowest  | 🔵    | **Minor**    | Style issues, naming inconsistencies, missing docs/comments, code that works but is fragile, dead code, small inefficiencies                                          |

**Rules**:

- Every issue MUST be assigned exactly one severity level.
- Do NOT invent issues. Only flag real problems visible in the diff.
- If a single code block has multiple problems, create a separate issue block for each.
- Severity is non-negotiable based on the impact, not the author's intent.

---

## Impact Scope Definitions

Choose the narrowest scope that is accurate:

| Scope           | Meaning                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| **Line**        | Affects only the changed line(s), no propagation                        |
| **Function**    | Affects callers of this function                                        |
| **Module**      | Affects the entire file/class/component                                 |
| **Service**     | Affects one microservice, API endpoint group, or major feature          |
| **System-wide** | Affects multiple services, cross-cutting concerns (auth, DB, messaging) |

---

## Data Compatibility Checklist

When reviewing ANY code that handles user input, stored data, API responses, or comparisons, check ALL of the following:

### Type Safety & Coercion

- [ ] Are values compared with strict equality (`===`) vs loose (`==`) where appropriate?
- [ ] Could JavaScript/Python type coercion silently produce wrong results? (e.g., `"0" == false`, `null == undefined`)
- [ ] Are numbers parsed before comparison? (e.g., form input `"10"` vs integer `10`)
- [ ] Could `NaN` or `Infinity` propagate silently?

### Null / Undefined / Empty Values

- [ ] Are null/undefined inputs guarded before use?
- [ ] Does the code handle empty strings `""` vs `null` vs `undefined` distinctly where required?
- [ ] Could optional chaining or nullish coalescing prevent crashes?

### String & Encoding

- [ ] Are string comparisons case-sensitive when they should be case-insensitive (or vice versa)?
- [ ] Are locale-specific comparisons used for user-visible text? (e.g., `localeCompare` vs `<`)
- [ ] Are Unicode / emoji / multi-byte characters handled correctly?
- [ ] Is user input trimmed of whitespace before comparison or storage?
- [ ] Are encodings (UTF-8, Base64, URL-encoding) consistent between producer and consumer?

### Date & Time

- [ ] Are dates compared as Date objects or strings? (string comparison of dates is unreliable)
- [ ] Are timezones and UTC offsets accounted for?
- [ ] Is epoch milliseconds vs seconds confusion possible?

### Schema & API Compatibility

- [ ] Does this change break backward compatibility with existing stored data or API consumers?
- [ ] Are default values provided for newly added required fields (migration safety)?
- [ ] Are removed or renamed fields handled gracefully in old clients / DB rows?

### Boundary & Range

- [ ] Are numeric ranges validated before use? (off-by-one, negative values where only positive expected)
- [ ] Could integer overflow / underflow occur?
- [ ] Are array indices guarded against out-of-bounds access?

---

## Review Workflow

1. **Read the full diff first** — understand intent before judging defects.
2. **Identify all issues** — do not stop at the first critical problem.
3. **Classify each issue** by severity and scope.
4. **Run the Data Compatibility Checklist** on every function that handles external/user data.
5. **Write issue blocks** in severity order: Critical → Major → Minor.
6. **Write the Data Compatibility Analysis section** even if no issues are found.
7. **Write the Verdict**.

---

## Tone & Communication

- Be direct and specific. Reference actual lines / variable names from the diff.
- Do NOT be harsh or personal. Frame issues as engineering observations.
- For each issue, always provide a fix or at least a concrete direction — never just "this is wrong."
- If the diff is ambiguous (e.g., missing context), note what assumption you made.
- If the change is good, say so in the Verdict. Positive reinforcement matters.

---

## Examples of Data Compatibility Issues to Catch

```javascript
// ❌ BAD: loose equality, "0" == false is true in JS
if (userInput == false) { ... }

// ✅ GOOD
if (userInput === false) { ... }
```

```python
# ❌ BAD: case-sensitive comparison on user-supplied email
if user_email == stored_email:

# ✅ GOOD
if user_email.strip().lower() == stored_email.strip().lower():
```

```javascript
// ❌ BAD: date as string comparison
if (startDate < endDate)  // "2024-12-01" < "2024-02-01" is FALSE (string sort)

// ✅ GOOD
if (new Date(startDate) < new Date(endDate))
```

```python
# ❌ BAD: no null guard on user input
result = int(request.args.get("page")) * PAGE_SIZE

# ✅ GOOD
page = request.args.get("page", "1")
result = int(page) * PAGE_SIZE  # still needs try/except
```

---

## Output Language

Respond in the **same language the user uses** unless they specify otherwise. Technical identifiers (variable names, function names) always stay in their original form.---
name: code-review
description: >
Perform structured, severity-graded code reviews on changed/diff code. Use this skill whenever
the user submits a code diff, patch, pull request snippet, or says "review my code", "check this
change", "LGTM?", "can you review", "code review", or pastes before/after code blocks. Also trigger
when the user asks about potential bugs, security issues, or data compatibility problems in code.
Always apply this skill even for small snippets — every change deserves a graded review.

---

# Code Review Skill

A structured skill for reviewing code changes with severity grading, impact scoping, and data compatibility analysis.

---

## Review Output Format

Every review MUST follow this exact structure:

### 1. Summary Header

```
## Code Review — [filename or feature description]
Reviewed: [N] issues — 🔴 Critical: X  |  🟡 Major: Y  |  🔵 Minor: Z
```

### 2. Issue Blocks (one per finding)

```
### [SEVERITY EMOJI] [SEVERITY LABEL] — [Short Issue Title]

**Location**: [file:line or function name or code excerpt]
**Impact Scope**: [Line / Function / Module / Service / System-wide]
**Potential Impact**: [What can go wrong — bugs, data loss, security breach, UX breakage, etc.]

**Problem**:
[Clear explanation of the defect. Reference the actual code.]

**Fix / Recommendation**:
[Concrete code suggestion or remediation steps]

---
```

### 3. Data Compatibility Section (mandatory)

Always include a dedicated section at the end:

```
## 🔄 Data Compatibility Analysis

[Findings on type coercion, null/undefined handling, encoding issues, locale-sensitive comparisons,
user-supplied input edge cases, schema migrations, backward compatibility, etc.]

If no issues found, still confirm: "✅ No data compatibility issues detected."
```

### 4. Overall Verdict

```
## Verdict
[APPROVE / REQUEST CHANGES / NEEDS DISCUSSION]
[1–3 sentence summary of the overall state of the diff and recommended next steps]
```

---

## Severity Definitions

| Level       | Emoji | Label        | When to Use                                                                                                                                                           |
| ----------- | ----- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 — Highest | 🔴    | **Critical** | Data loss, security vulnerabilities (injection, auth bypass, exposure of PII), crashes in production, breaking API contracts, silent data corruption                  |
| 2 — Medium  | 🟡    | **Major**    | Logic errors that produce wrong results under realistic inputs, race conditions, missing error handling on important paths, performance cliffs, incorrect comparisons |
| 3 — Lowest  | 🔵    | **Minor**    | Style issues, naming inconsistencies, missing docs/comments, code that works but is fragile, dead code, small inefficiencies                                          |

**Rules**:

- Every issue MUST be assigned exactly one severity level.
- Do NOT invent issues. Only flag real problems visible in the diff.
- If a single code block has multiple problems, create a separate issue block for each.
- Severity is non-negotiable based on the impact, not the author's intent.

---

## Impact Scope Definitions

Choose the narrowest scope that is accurate:

| Scope           | Meaning                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| **Line**        | Affects only the changed line(s), no propagation                        |
| **Function**    | Affects callers of this function                                        |
| **Module**      | Affects the entire file/class/component                                 |
| **Service**     | Affects one microservice, API endpoint group, or major feature          |
| **System-wide** | Affects multiple services, cross-cutting concerns (auth, DB, messaging) |

---

## Data Compatibility Checklist

When reviewing ANY code that handles user input, stored data, API responses, or comparisons, check ALL of the following:

### Type Safety & Coercion

- [ ] Are values compared with strict equality (`===`) vs loose (`==`) where appropriate?
- [ ] Could JavaScript/Python type coercion silently produce wrong results? (e.g., `"0" == false`, `null == undefined`)
- [ ] Are numbers parsed before comparison? (e.g., form input `"10"` vs integer `10`)
- [ ] Could `NaN` or `Infinity` propagate silently?

### Null / Undefined / Empty Values

- [ ] Are null/undefined inputs guarded before use?
- [ ] Does the code handle empty strings `""` vs `null` vs `undefined` distinctly where required?
- [ ] Could optional chaining or nullish coalescing prevent crashes?

### String & Encoding

- [ ] Are string comparisons case-sensitive when they should be case-insensitive (or vice versa)?
- [ ] Are locale-specific comparisons used for user-visible text? (e.g., `localeCompare` vs `<`)
- [ ] Are Unicode / emoji / multi-byte characters handled correctly?
- [ ] Is user input trimmed of whitespace before comparison or storage?
- [ ] Are encodings (UTF-8, Base64, URL-encoding) consistent between producer and consumer?

### Date & Time

- [ ] Are dates compared as Date objects or strings? (string comparison of dates is unreliable)
- [ ] Are timezones and UTC offsets accounted for?
- [ ] Is epoch milliseconds vs seconds confusion possible?

### Schema & API Compatibility

- [ ] Does this change break backward compatibility with existing stored data or API consumers?
- [ ] Are default values provided for newly added required fields (migration safety)?
- [ ] Are removed or renamed fields handled gracefully in old clients / DB rows?

### Boundary & Range

- [ ] Are numeric ranges validated before use? (off-by-one, negative values where only positive expected)
- [ ] Could integer overflow / underflow occur?
- [ ] Are array indices guarded against out-of-bounds access?

---

## Review Workflow

1. **Read the full diff first** — understand intent before judging defects.
2. **Identify all issues** — do not stop at the first critical problem.
3. **Classify each issue** by severity and scope.
4. **Run the Data Compatibility Checklist** on every function that handles external/user data.
5. **Write issue blocks** in severity order: Critical → Major → Minor.
6. **Write the Data Compatibility Analysis section** even if no issues are found.
7. **Write the Verdict**.

---

## Tone & Communication

- Be direct and specific. Reference actual lines / variable names from the diff.
- Do NOT be harsh or personal. Frame issues as engineering observations.
- For each issue, always provide a fix or at least a concrete direction — never just "this is wrong."
- If the diff is ambiguous (e.g., missing context), note what assumption you made.
- If the change is good, say so in the Verdict. Positive reinforcement matters.

---

## Examples of Data Compatibility Issues to Catch

```javascript
// ❌ BAD: loose equality, "0" == false is true in JS
if (userInput == false) { ... }

// ✅ GOOD
if (userInput === false) { ... }
```

```python
# ❌ BAD: case-sensitive comparison on user-supplied email
if user_email == stored_email:

# ✅ GOOD
if user_email.strip().lower() == stored_email.strip().lower():
```

```javascript
// ❌ BAD: date as string comparison
if (startDate < endDate)  // "2024-12-01" < "2024-02-01" is FALSE (string sort)

// ✅ GOOD
if (new Date(startDate) < new Date(endDate))
```

```python
# ❌ BAD: no null guard on user input
result = int(request.args.get("page")) * PAGE_SIZE

# ✅ GOOD
page = request.args.get("page", "1")
result = int(page) * PAGE_SIZE  # still needs try/except
```

---

## Output Language

Respond in the **same language the user uses** unless they specify otherwise. Technical identifiers (variable names, function names) always stay in their original form.
