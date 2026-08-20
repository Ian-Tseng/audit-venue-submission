# General Venue-Submission Audit Guide

## Purpose

Use this venue-neutral guide for journals, conferences, revisions, supplements, and camera-ready packages. Current official instructions override this guide.

Maintain three layers:

1. **General core:** stable cross-venue audit principles.
2. **Venue overlay:** current rules for one venue, year, track, article type, and stage.
3. **Submission instance:** exact files, author decisions, hashes, portal state, failures, and receipts.

Do not duplicate venue-specific rules into the general core.

## Source-Backed Top-Tier Writing Evidence

When asked to search for or apply top-tier writing guidance, browse current first-party author, reviewer, checklist, and track pages. Log the page title, exact URL, access date, extracted rule, and whether it is a binding venue rule or a reusable heuristic. Cite the direct page rather than a search-result URL. Refresh time-sensitive venue details before every venue-specific refinement and again before submission; update the relevant Markdown guide/log/check-table elements before running the post-refinement inconsistency audit.

Baseline first-party evidence, last checked **2026-08-20 (Asia/Taipei)**:

| Source | Reusable evidence-backed check | Boundary |
|---|---|---|
| [Nature Portfolio: How to write your paper](https://www.nature.com/nature-portfolio/for-authors/write) | Prefer direct active sentences; avoid unnecessary jargon/acronyms; keep one focused main message; move supporting technical detail to Supplementary Information with signposts. | General writing heuristic; exact target-journal rules override it. |
| [Nature: Initial submission](https://www.nature.com/nature/for-authors/initial-submission) | Make the abstract a brief non-technical statement of results and implications; make Methods sufficient for interpretation and replication; use descriptive table titles and standalone figure legends. | Nature's approximate summary/display limits are not universal. |
| [NeurIPS 2026 Call for Papers](https://neurips.cc/Conferences/2026/CallForPapers) | Preserve rigorous analyses of limitations and behavior beyond the headline setting as scientific evidence. | Use the applicable track call for binding rules. |
| [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist) | Check reproducibility, transparency, research ethics, and societal-impact boundaries explicitly. | Checklist packaging is venue/year specific. |
| [AAAI-26 Reproducibility Checklist](https://aaai.org/conference/aaai/aaai-26/reproducibility-checklist/) | Include a conceptual method outline and distinguish objective facts/results from opinions, hypotheses, and speculation. | Recheck the target year's official checklist before upload. |

Convert the accepted evidence into task-specific gates:

- title/abstract: what was found, why it matters, and the central limitation are visible without inflated advocacy;
- opening: the research problem and question precede implementation inventory;
- prose: direct sentences, stable terminology, and only necessary acronyms/jargon;
- displays: each item earns its place, has a nearby callout, and has a standalone caption;
- Methods: inputs, access, operations, outputs, evaluation, and replication detail are recoverable;
- Results/Discussion: direct observations remain separate from interpretation, speculation, and deployment implications;
- evidence economy: the main paper carries the argument and compact evidence while appendices/supplements carry supporting detail;
- transparency: limitations, counterevidence, reproducibility, ethics, and societal-impact boundaries are paper-visible.

After any authorized revision, rebuild affected artifacts and rerun these writing gates together with claim, terminology, equation, citation, layout, anonymity, archive, and hash checks. Repair active local `FAIL` or `PARTIAL` results and repeat until the local package converges. Keep genuine portal/user/external actions `PENDING`.

## Element-Level Venue Contract

Convert every subject in the current official guide or author-kit table of contents into one independent requirement element. For each element, record:

- stable ID and official subject label;
- applicability to the current article/stage;
- testable paraphrase of the rule;
- target manuscript artifact, upload item, metadata field, or post-decision action;
- evidence or next action, status, and last-checked date.

Include Aims and scope, Article types, Peer review, Special issues or article collections, ethics/policies, every writing/formatting and reference subtopic, submission/portal checks, post-decision requirements, and author resources. Keep the complete matrix separate from the concise paper-specific blocker table; link them through a summary row and update affected elements during every refinement. Do not copy the source guide at length: paraphrase auditable requirements and retain direct first-party links.

## Minimum Venue Profile

Record the following in a venue overlay or audit report:

| Field | Required record |
|---|---|
| Target | Venue, year, track, article type, submission stage |
| Evidence | Official URL, page title, access date, downloaded template/version/hash |
| Timing | Deadline, timezone, abstract/full-paper distinction |
| Review | Anonymous/single-blind/double-blind/identified and title-page handling |
| Length | Main text, abstract, references, appendix, figures/tables, supplement |
| Format | Template, style version, page size, columns, fonts, source type, build tool |
| Files | Required and optional upload roles, extensions, sizes, naming rules |
| Declarations | Conflicts, funding, CRediT, AI use, ethics, consent, data/code availability |
| Portal | Metadata fields, author accounts, ORCID, corresponding-author behavior, approvals |
| Policies | Preprints, repositories, external links, supplementary data, AI-generated media |

When an official public guide and live portal differ, record both. Use the portal for current field behavior and the venue guide for substantive policy unless a higher-authority instruction resolves the conflict.

## Artifact Roles

Maintain one canonical artifact per role:

- anonymous manuscript;
- identified title page or author manuscript;
- abstract, title, keywords, and other portal metadata;
- supplement document and/or archive;
- mandatory declaration or reporting form;
- highlights, graphical abstract, cover letter, response letter, source archive, or media when applicable.

Label drafts, author copies, old venues, screenshots, logs, and reviewer exports as non-upload artifacts. Exclude them from active inconsistency results unless they can realistically guide a mistaken upload.

## Audit Gates

### Contract

- Target and submission stage are explicit.
- Current primary sources are saved with dates.
- Required and optional fields are distinguished.
- Conflicts among sources are logged.

### Content

- Central claims map to protocols, datasets, metrics, and limitations.
- Negative results and metric tradeoffs are preserved.
- Deployment, human-study, external-validity, and causal limits are direct.
- Named datasets, models, methods, and nonstandard metrics have citations.

### Template and Build

- The current official template/style is used.
- No generic visual imitation or prohibited layout shortcut is used.
- Build commands, versions, bibliography cycle, and warnings are recorded.
- Anonymous and identified sources are separate where required.

### Generated Manuscript

- Page/word allocation and page size pass.
- Fonts are embedded and glyphs render.
- Display and inline mathematics are both native and readable: Word uses `m:oMathPara` for displays and inline `m:oMath` in prose/captions/tables; PDF text and visual checks show real superscripts, subscripts, and Greek symbols rather than caret or spelled-name fallbacks.
- No clipping, overflow, unexpected blank page, duplicate page, or unreadable table exists.
- Metadata, headers, acknowledgements, file paths, and links do not break anonymity.
- Every page is rendered and visually inspected.

### Supplements and Archives

- ZIP entries have no traversal or absolute paths.
- No credentials, private paths, author identity, caches, `.pyc`, or unintended checkpoints exist.
- README, manifest, hashes, filenames, entry counts, and external-artifact boundaries agree.
- Packaged scripts parse/import; at least one package-only command runs when inputs permit.

### Cross-Artifact Synchronization

Compare exact title, abstract, keywords, author order, affiliations, corresponding author, datasets, counts, seeds, metrics, protocols, limitations, table values, mathematical notation, supplement filenames, and hashes. Distinguish pooled metrics from per-source means and label intentional differences. Require the same inline mathematical meaning and structure across Markdown/LaTeX, native Word OMML, HTML MathML, and the rendered PDF.

### Terminology Contract and Display Alignment

Create one terminology contract before the final refinement pass. Each contract entry should record:

| Field | Meaning |
|---|---|
| `id` | Stable machine-facing key for one scientific concept |
| `canonical` | Preferred reader-facing phrase |
| `forbidden_variants` | Legacy, ambiguous, or near-synonymous phrases that should not reappear |
| `required scopes` | Abstract, method, figure labels, figure caption, table, supplement, metadata, or generated artifact locations that must use the phrase |
| `require_mode` | `scope` checks the combined scope; `each_file` requires the canonical phrase in every selected active file |
| `allowed variants` | Controlled short forms or scope-specific wording with a stated reason |

Align the same concept across:

- main-text definition and later prose;
- section/subsection heading;
- figure box or axis label, figure caption, and textual callout;
- table title, row/column labels, notes, and textual callout;
- appendix/supplement inventory and reproducibility instructions;
- title/abstract/keywords/highlights/portal metadata when the concept appears there;
- generated DOCX/PDF and peer-review/upload derivatives.

Use a source file, SVG, or label transcript to audit image-only figure text, then visually inspect the rendered figure. OCR may support discovery but does not replace checking the authoritative label source. Preserve legitimate distinctions: for example, a protocol, its normalization operation, and its evaluation set may need different names. Define acronyms at first substantive use in each independently readable scope and keep capitalization, hyphenation, mathematical symbols, metric names, and dataset names stable afterward.

Run:

```text
python scripts/audit_terminology.py --root <workspace> --contract <contract.json> --output <report.json>
```

A passing script result is necessary but not sufficient: confirm that figure/table labels remain readable and unchanged in the final rendered PDF and portal-generated proof.

### Portal and Final State

- Authors, order, emails, affiliations, ORCIDs, funding, CRediT, conflicts, and declarations are complete.
- Files are mapped to the correct item types.
- The portal-generated manuscript is opened and inspected.
- Final submission status, manuscript identifier, receipt, file inventory, and hashes are retained.

## Anonymity Matrix

| Information | Anonymous review file | Identified title page/portal |
|---|---|---|
| Names and affiliations | Exclude | Include |
| Emails, ORCIDs, phone | Exclude | Include as required |
| Funding identifiers | Exclude when identity revealing | Include in requested field/file |
| Acknowledgements | Omit or anonymize per rule | Include when applicable |
| Self-citations | Follow venue rule; avoid identity-revealing phrasing | Normal form when allowed |
| Repository links | Use anonymous link only if permitted | Use final public link when allowed |
| File/PDF metadata | Sanitize | Verify accuracy |

## Status and Readiness

Use `PASS`, `FAIL`, `PARTIAL`, `PENDING`, `NA`, or `BLOCKED`. Each non-pass row needs an owner, exact action, and evidence needed to close it.

Report readiness at three levels:

1. **Source readiness:** canonical editable sources are internally consistent.
2. **Local package readiness:** generated upload files pass format and content audits.
3. **Submission readiness:** portal fields, generated proof, approval, and receipt are complete.

Do not collapse these levels into one “ready” claim.

## Recommended Finding Table

| ID | Gate | Status | Evidence | Risk | Owner/next action |
|---|---|---|---|---|---|
| `[id]` | `[specific check]` | `[status]` | `[file, URL, log, or portal observation]` | `[blocker/advisory]` | `[action]` |

## Iterative Convergence

After an authorized update, rebuild and synchronize its active dependents, then rerun the relevant venue, claim, terminology, equation, metadata, anonymity, archive, and hash checks. Repair any remaining active local `FAIL` or `PARTIAL` and repeat until the local package converges. Keep audit-only requests read-only, preserve immutable reviews and archives, and report portal-, user-, or external-dependent `PENDING` or `BLOCKED` items separately.

## Final Handoff

State:

- what changed;
- what was rebuilt and inspected;
- exact upload filenames and hashes;
- remaining author, editor, or portal actions;
- whether a binary must be uploaded again;
- whether the local package and saved portal submission independently pass.
