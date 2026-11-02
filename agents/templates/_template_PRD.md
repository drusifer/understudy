<!--
Product Requirements Document template. Owned by Cypher (Product Manager) — see agents/cypher/SKILL.md.
Instantiated as `docs/PRD.md`. It says what the product is for, who it serves and what it must do; it does
not say how (architecture, ADRs) or when (the sprint task board).
Remove this note and the check block when creating a real artifact; checks belong to templates.
Reviewed by Smith (user value) and Morpheus (feasibility) using the PRD check.
-->
# Product Requirements: {Product Name}

*   **Status**: {Draft | Active | Superseded}
*   **Owner**: Cypher (*pm), for {the person who owns the product}
*   **Last Updated**: {YYYY-MM-DD}
*   **Related**: {domain model, architecture, SDLC, decisions: links}

---

## 1. Vision and Problem

{Two to four sentences: what the product is, the problem it removes, and why that matters to the people who
have it. No implementation.}

* **For** {who}, **who** {need}, **{Product}** is {what it is} **that** {main benefit}. **Unlike** {the alternative they use today}, it {key difference}.

## 2. Users and Their Jobs

| User | Job they are trying to get done | Today they | Success looks like |
|---|---|---|---|
| **{User or role}** | {The outcome they want} | {How they do it now and what hurts} | {What they can say afterwards} |

## 3. Goals and How We Will Know

| # | Goal (an outcome, not a feature) | Measure | Target | Source of the number |
|---|---|---|---|---|
| G1 | {outcome} | {observable measure} | {value, or "owner to set"} | {where it is read from} |

## 4. Non-Goals

- {Something a reader might expect the product to do, that it will not, and why.}

## 5. Principles and Constraints

{Rules the owner gave that every requirement must respect, each with where it was recorded.}

| # | Principle or constraint | Recorded in |
|---|---|---|
| P1 | {rule} | {file or decision} |

## 6. Requirements

Each requirement is one observable capability a tester could check. Status: **Delivered** (sprint), **Planned** (sprint),
or **Open** (not scheduled). Link the story or decision that holds the detail instead of copying it.

### 6.1 {Capability area}

| ID | Requirement | Priority | Status | Detail |
|---|---|---|---|---|
| R1 | {The product shall … (observable)} | {Must / Should / Could} | {Delivered S{n} / Planned S{n} / Open} | {story id, ADR or doc} |

### 6.2 Quality attributes

| ID | Attribute | Requirement | Status | Detail |
|---|---|---|---|---|
| Q1 | {Privacy, reproducibility, usability, performance, security …} | {Measurable statement} | {status} | {link} |

## 7. Release Path

| Release or sprint | Outcome for the user | Requirements |
|---|---|---|
| {name} | {what is true afterwards} | {R-ids} |

## 8. Risks and Open Questions

| # | Risk or question | Who can answer | Assumed until then |
|---|---|---|---|
| 1 | {question} | {persona or owner} | {assumption} |

<!-- RUBRIC-START -->
## Check — PRD

- [ ] **PASS** — `PROBLEM`: The vision names who has the problem and what it costs them, without naming an implementation.
- [ ] **PASS** — `USERS`: Every user has a job, a current way of doing it, and a recognizable success.
- [ ] **PASS** — `GOALS`: Every goal is an outcome with an observable measure and a target or an explicit "owner to set".
- [ ] **PASS** — `SCOPE`: Non-goals list things a reader might expect, and principles cite where the owner said them.
- [ ] **PASS** — `REQS`: Every requirement is one observable behavior, has a priority and a truthful status, and links its story, decision or doc; none describes a design.
- [ ] **PASS** — `TRACE`: Every Delivered requirement can be found in the code, docs or tests; every Planned one is in a sprint's stories.
- [ ] **FAIL** — Any required PASS condition is unmet or unsupported; cite the missing evidence and smallest correction.
<!-- RUBRIC-END -->
