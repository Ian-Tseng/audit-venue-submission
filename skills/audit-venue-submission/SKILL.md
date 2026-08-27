---
name: audit-venue-submission
description: Audit scholarly manuscripts and submission packages against current venue requirements, cross-section claim chains, and a canonical terminology contract. Use when checking venue format, anonymity, page or word limits, templates, declarations, author metadata, portal upload roles, DOCX/PDF/TeX output, supplements, claim continuity from research question through protocol, result, counterevidence, and boundary, cross-artifact consistency, run-aware word/paragraph alignment, terminology across prose, headings, figures, captions, tables, metadata, and generated artifacts, submission readiness, desk-rejection remediation, or venue adaptation.
license: MIT
---

# Audit Venue Submission

Audit the saved submission package, not only its editable source. Treat current official venue instructions and the live portal as time-sensitive evidence.

## Start

1. Read [references/general-guide.md](references/general-guide.md) completely.
2. Read applicable repository instructions and identify the canonical manuscript, generated files, supplement, metadata, and check table.
3. Record the target venue, year, track, article type, review stage, and audit date. Do not infer missing values from an old filename.
4. Browse the current official venue, publisher, author-kit, and submission-system sources. Prefer primary sources and cite or log the exact URLs and access date. If the portal exposes rules unavailable publicly, label them as portal-observed evidence.
5. When a user requests top-tier, Nature-style, NeurIPS-style, or AAAI-style writing guidance, use the source-backed workflow in [references/general-guide.md](references/general-guide.md): refresh current first-party sources, log exact URLs and access dates, distinguish reusable heuristics from binding venue rules, and convert accepted guidance into testable manuscript gates.
6. Separate the venue-neutral core, venue overlay, and submission-instance record. Never convert one venue's rule into a universal requirement.

## Confirm confidential intake before reading unpublished content

Before processing an unpublished manuscript, peer-review file, portal export,
author data, or restricted submission package, confirm authorization,
confidentiality policy, current venue AI policy, permitted AI assistance,
human accountability, conflicts handling, retention, and local-only
processing. Do not place manuscript text, reviewer text, author identities,
private paths, credentials, or unpublished results in web searches, issue
drafts, telemetry, or quality receipts.

Read
[references/confidential-intake-and-reporting-guidelines.md](references/confidential-intake-and-reporting-guidelines.md)
completely when intake or study-design reporting guidance is in scope. Validate
one local intake record and select candidate guidelines with:

```text
<python-3> "<skill-root>/scripts/submission_intake.py" validate --intake <local-intake.json>
<python-3> "<skill-root>/scripts/submission_intake.py" guidelines --study-design <design>
```

The helper reads no manuscript, makes no network request, echoes no submission
content, and never scores reporting compliance. Its candidates must be
reconfirmed against current first-party guideline, extension, and venue rules.

## Refresh official sources on every refinement

Treat official venue requirements as mutable. Before every venue-specific refinement, not only before final submission:

1. Re-open the current official venue, publisher-policy, author-kit, and accessible live-portal sources.
2. Compare the current rules with the active local contract; use the authority order below when they differ.
3. Record exact URLs, access date, retrieval limitations, and changed requirements in the relevant active Markdown guide, timing/source log, and affected check-table items.
4. Synchronize any changed rule across canonical source, generated artifacts, upload copies, and portal-role records.
5. Run the full relevant inconsistency audit; repair, update check-table evidence, rebuild, and repeat while any active local `FAIL` or `PARTIAL` remains.

If the official guide exposes a subject list or table of contents, represent each subject as an independent venue-contract element with a stable ID, applicability, testable requirement, target artifact or portal field, evidence/next action, status, and last-checked date. Include journal-fit subjects, ethics/policies, writing/formatting, references, portal/submission, special issues or collections, post-decision actions, and author resources. Keep this complete element matrix separate from the shorter paper-specific blocker table, but link the two and update affected rows during every refinement.

Do not silently treat an older cached rule as current when the official source can be checked. If a site is unavailable or access-controlled, record that limitation and the first-party surface actually used, such as the publisher page, indexed official page, downloaded author kit, or live portal observation.

## Respect the Requested Scope

- For `check`, `audit`, or `review`, inspect and report without changing files.
- For `fix`, `prepare`, or `make submission-ready`, edit only active artifacts, rebuild every affected output, and verify the rebuilt binaries.
- Preserve frozen submissions and provenance archives unless the user explicitly asks to change them.
- Ask only when a missing choice would materially change authorship, corresponding-author control, declarations, or the target contract.

## Build the Venue Contract

Capture, with source evidence:

- venue, year, track, article type, stage, deadline, and timezone;
- anonymity model and separate-title-page rules;
- official template/style, accepted source types, compiler or word processor, and page/word allocation;
- figure, table, reference, appendix, supplement, file-size, and external-link rules;
- mandatory declarations, forms, checklists, highlights, graphical abstracts, data/code statements, funding, CRediT, AI-use disclosure, ethics, and consent;
- applicable study-design reporting guideline candidates and extensions, with
  non-scoring coverage states and human-verified evidence locators;
- portal fields, author-profile requirements, corresponding-author behavior, conflicts, reviewer nominations, and required/optional upload item types.

Use this authority order when sources conflict:

1. Direct editor/chair instruction for this submission
2. Current track or article-type call
3. Current official author kit or journal guide
4. Live submission portal for field and upload behavior
5. Publisher-wide guidance
6. Local guide, prior-year package, or memory

Record unresolved conflicts instead of silently choosing.

## Inventory Active Artifacts

Assign exactly one canonical file to each upload or portal role. Mark every other file as working, identified, anonymous, generated, internal, archived, or superseded. A filename containing `final` or `submit-ready` is not evidence of readiness.

Run the deterministic preflight on the selected files:

```text
python scripts/audit_submission.py --root <package-root> --file <relative-file> --file <relative-file> --identity <author-name> --stale-term <old-venue-name> --output <audit.json>
```

Use repeated `--file`, `--identity`, and `--stale-term` arguments. Review the JSON; the script is an evidence collector, not a substitute for official-rule or visual checks.

## Establish a terminology contract

Before calling a package internally consistent, define canonical reader-facing terms for the paper's protocols, datasets, metrics, method stages, model components, display labels, and claim boundaries. Treat each of these as a separate scope:

- title, abstract, keywords, headings, and main prose;
- figure labels, legends, captions, and nearby callouts;
- table titles, headers, cells, notes, and nearby callouts;
- appendix, supplement, metadata, highlights, and declarations;
- generated DOCX/PDF plus upload and peer-review derivatives.

Use `scripts/audit_terminology.py` with a JSON terminology contract. Require the same canonical phrase in every scope that represents the same concept; use `require_mode: "each_file"` when every active copy in one scope must contain it. List disallowed legacy or near-synonymous variants explicitly. Use a figure-generation source, SVG, or maintained figure-label transcript for image-only figures, because PNG pixels are not a reliable text-audit surface. After the source check passes, inspect the rendered figure and every generated page visually.

Do not force distinct concepts into one name. Record controlled short forms, acronyms, and scope-specific variants when they are scientifically necessary. A first-use definition does not authorize uncontrolled switching among protocol names later.

## Enforce the cross-section claim chain

A manuscript can be terminology-consistent and still make readers reconstruct its argument. For each material claim, audit this relation across the active source and generated artifacts:

`problem -> research question -> information condition/protocol -> operation and output -> result and same-scope counterevidence -> interpretation and boundary`

Use `audit-method-data-flow` for its full claim-chain workflow when available. Otherwise apply the same contract directly. Require protocol qualifiers before or with headline results; keep the evaluated source/population, label access, exposure condition, method output, metric, and comparator stable through Results and Discussion. Place the strongest same-scope null, reversal, or tradeoff beside the positive result it limits.

Audit active control files as well as the paper. A current-looking check table, metadata draft, working manuscript, or rebuild guide that retains superseded framing can restore an overclaim even when the current PDF is correct. Mark such active guidance as superseded or repair it; preserve true archives and received reviews unchanged.

Fail when an anchor merely appears somewhere but its role changes across sections, when a delayed qualifier makes an earlier sentence misleading, when Discussion broadens a diagnostic or source-exposed result into a deployment or source-exclusive claim, or when generated artifacts omit the decisive counterevidence or boundary.

## Run the word/paragraph artifact gate

For DOCX, reconstruct visible text by joining both prose `w:t` and Office Math `m:t` runs per paragraph rather than searching raw XML. Scan the main story, tables and text boxes, headers, footers, footnotes, and endnotes. Report comments, author replies, tracked insertions, and deleted text separately so immutable reviewer evidence is not confused with upload-facing prose.

Use the bundled `scripts/audit_docx_text_parts.py` helper to check exact headings, forbidden aliases, required phrases, and synchronized Word copies. It reports findings by OOXML part plus file and normalized-visible-text hashes.

Compare active copies using both file SHA-256 and visible-text hashes. Treat received reviewer files and archives as provenance scopes; do not fail an upload merely because an immutable reviewer comment quotes old wording. Fail when the active visible body or an author reply contains a forbidden alias, an exact heading differs, a required phrase is missing, or a copied upload/Downloads artifact is stale.

For PDF, normalize extraction artifacts such as soft hyphens and line-wrap hyphenation before word-sequence comparison, but preserve meaningful wording, numbers, signs, and protocol qualifiers. Text extraction supports this gate; it does not replace visual page inspection. Audit inline mathematics separately from display equations: Word must use native inline `m:oMath`, HTML/PDF must render superscripts, subscripts, Greek symbols, and variables mathematically, and plaintext or corrupted forms such as `b(x)^2`, `phi(x)`, `p1(x)`, or `?(x)` fail active artifacts.

## Audit the Content and Format

Check all applicable gates:

- title, abstract, keywords, author order, affiliations, correspondence, and article type agree;
- claims, protocols, datasets, metrics, table values, limitations, citations, and supplement references agree;
- each material claim preserves its problem-to-boundary chain across Introduction, Methods, Results, Discussion, active guidance, and generated artifacts;
- canonical terms align across prose, headings, figure labels/captions, table titles/headers/cells, supplements, metadata, DOCX, and PDF;
- current official template and permitted build path are used without margin, font, spacing, or float shortcuts;
- required declarations and author information appear only in the correct anonymous or identified artifact;
- required upload roles are present and optional items have explicit include/omit decisions;
- source, generated DOCX/PDF, supplement, and portal metadata are synchronized;
- PDF page size, count, fonts, metadata, security, links, glyphs, tables, captions, references, and blank pages pass;
- display and inline mathematics pass independently across source, DOCX, HTML, and PDF; a correct display equation cannot mask plaintext inline formulas;
- ZIP entries are safe, anonymous where required, free of caches/credentials/private paths, and operationally reproducible.

Render and visually inspect every page after the last upload-facing rebuild. Inspect portal-generated PDFs separately because conversion can change layout.

## Classify Findings

Use only these statuses:

- `PASS`: verified by current evidence.
- `FAIL`: a rule is violated or an active artifact is inconsistent.
- `PARTIAL`: some evidence exists, but a required component is incomplete.
- `PENDING`: requires a future portal/user/external action.
- `NA`: demonstrably inapplicable, with a reason.
- `BLOCKED`: completion is impossible without missing authority or access.

Distinguish:

- upload blocker;
- portal/admin blocker;
- content or evidence risk;
- advisory improvement;
- harmless archived or contingency wording.

Do not call a package submission-ready while any mandatory row is `FAIL`, `PARTIAL`, `PENDING`, or `BLOCKED`. Local artifact readiness and completed submission-system readiness are separate claims.

## Fix and Rebuild

When authorized to fix:

1. Update the canonical source and the active check table.
2. Rebuild every affected PDF, DOCX, HTML, ZIP, or source archive using the recorded official build path.
3. Re-run text, metadata, anonymity, archive, citation, and cross-artifact scans.
4. Re-run the terminology contract and resolve unapproved variants in every affected scope.
5. Re-run the source-backed writing gates that apply: problem-first framing, cross-section claim-chain continuity, abstract result/implication/limitation balance, direct sentences, controlled jargon/acronyms, main/supplement economy, standalone captions, reproducible Methods, explicit counterevidence, and fact-versus-speculation boundaries.
6. Render and inspect every generated page, including image-only figure labels and table text.
7. Record filenames, bytes, SHA-256 hashes, page counts, and exact remaining portal actions.
8. Re-upload only artifacts whose binaries or required dependencies changed.

## Iterate to a Clean Active State

After every authorized repair, use iterative convergence by default:

1. Refresh the official sources, then update the canonical active source, relevant Markdown contract/log, affected check-table items, and all dependent records.
2. Rebuild and synchronize every affected generated or upload-facing artifact.
3. Re-run the full relevant inconsistency audit, including claim boundaries, terminology, equations, anonymity, package contents, and hashes.
4. If any active local `FAIL` or `PARTIAL` remains, repair it and repeat the loop.

Stop successfully only when no active local `FAIL` or `PARTIAL` remains. Report genuine portal-, user-, or external-dependent `PENDING` or `BLOCKED` items explicitly rather than treating them as local inconsistencies. Keep immutable received reviews and provenance archives unchanged unless the user specifically asks to revise them.

## Report

Lead with the outcome. Include:

- target contract and evidence date;
- fixed inconsistencies;
- remaining blockers with owner and next action;
- verified artifact inventory and hashes when relevant;
- explicit readiness state: local files, portal state, and overall submission.

Never hide uncertainty, treat a successful build as proof of compliance, or infer that funding pays an APC without confirmation.

## Finish with managed maintenance and one quality receipt

After completing the substantive audit and immediately before the final
response, run:

```text
<python-3> <skill-root>/scripts/update_policy.py --format json maintain
```

Maintenance is consent-gated, leased, and restricted to one clean, unpinned,
user-scope GitHub CLI installation from `Ian-Tseng/audit-venue-submission`.
It must not replace or shorten the audit. Append its `message` and `action`
only when `emit` is true; a verified replacement activates on the next
invocation.

Then emit exactly one content-free outcome receipt:

```text
<python-3> <skill-root>/scripts/skill_outcome.py --format json emit \
  --outcome <completed|completed_with_limitations|failed> \
  --quality-signal <claim_evidence_gap|lifecycle_inconsistency|documentation_mismatch|internal_failure|no_issue>
```

Append only the returned `SKILL_OUTCOME_RECEIPT_V1:` marker as the final line.
Use `no_issue` when no reusable skill-quality follow-up is warranted. The
marker contains no manuscript, finding, path, prompt, log, or patch. It permits
an installed `analyze-project-claims` adapter to create one local proposal;
it never authorizes an issue, edit, update, merge, release, or upload. Any
public issue remains a separate, twice-confirmed action restricted to the
`Ian-Tseng` owner boundary.

Repository-side repair is separate from this invocation. An owner-reviewed
`managed-repair-ready` issue may enter the full-SHA-pinned central workflow,
but the label is eligibility only: protected environments separately approve
credential-free candidate work and draft publication. The workflow cannot
accept evidence, merge, release, publish, update this installation, or prove
fresh activation. Never bypass the native updater or send project content as
feedback.
