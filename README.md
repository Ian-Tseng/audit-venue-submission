# Audit Venue Submission

Audit Venue Submission checks scholarly manuscripts and saved submission
packages against current venue rules, cross-section claim chains, terminology,
anonymity, generated artifacts, and portal roles.

The skill separates three claims that are often blurred:

- source readiness;
- local upload-package readiness;
- completed submission-system readiness.

It never treats a successful build as proof of compliance and never submits to
a journal or conference portal on the user's behalf.

## Install

Install the public standalone skill for Codex:

    gh skill install Ian-Tseng/audit-venue-submission skills/audit-venue-submission/SKILL.md --agent codex --scope user

Install the same package for Claude Code:

    gh skill install Ian-Tseng/audit-venue-submission skills/audit-venue-submission/SKILL.md --agent claude-code --scope user

Then start a fresh client session. In Codex, invoke:

    $audit-venue-submission audit this saved submission package for <venue>,
    <year>, <track>, <article type>, and <review stage>

In Claude Code, confirm the skill is visible in /skills, then invoke
/audit-venue-submission with the same target details. Installation proves
managed distribution; client discovery and a real invocation remain separate
runtime checks.

## Update

Updates remain user-controlled. The installed skill asks once before enabling
notification or automatic replacement, verifies one clean GitHub-managed
user installation, and checks through a 24-hour lease after substantive use:

    gh skill update audit-venue-submission --dry-run
    gh skill update audit-venue-submission

Pin a reproducible installation when needed:

    gh skill install Ian-Tseng/audit-venue-submission skills/audit-venue-submission/SKILL.md --agent codex --scope user --pin v0.1.1

This release has a consent-gated managed updater and a content-free quality
receipt. Both run after the substantive result and never authorize telemetry,
issue submission, file upload, or feedback transport. A compatible
`analyze-project-claims` adapter may create one local proposal; any public
issue requires separate exact approval.

## Local evidence helpers

The package contains deterministic local collectors:

- audit_submission.py: selected-file hashes, DOCX/PDF/ZIP facts, identity,
  stale-term, placeholder, archive-path, cache, and secret-category checks;
- audit_terminology.py: canonical and forbidden terminology across active
  scopes;
- audit_docx_text_parts.py: visible, inserted, deleted, and comment surfaces
  across Word parts;
- package_integrity.py: package manifest build and verification.

All selected inputs and outputs are constrained to the declared root. The
helpers do not browse or submit anything. Venue-specific audits must still
refresh current first-party sources and visually inspect every generated page.

The Python standard library covers text, DOCX, and ZIP checks. PDF text and
metadata inspection is enhanced when the optional pypdf package is installed;
its absence is reported as an evidence gap rather than silently treated as a
pass.

## GitHub-managed repair boundary

This repository carries one closed policy and one thin caller pinned to analyzer
workflow commit `f15311473e33d15f0ab9eee5a4bfca385ff4c5db`. It copies no central repair implementation. A
label is triage eligibility only; protected environments gate the agent and
draft publication separately. Repair remains disabled until method passes its
hosted canary and venue provisioning is read back.

See the immutable [managed fleet quickstart](https://github.com/Ian-Tseng/analyze-project-claims/blob/f15311473e33d15f0ab9eee5a4bfca385ff4c5db/docs/MANAGED_FLEET_QUICKSTART.md)
and [operations runbook](https://github.com/Ian-Tseng/analyze-project-claims/blob/f15311473e33d15f0ab9eee5a4bfca385ff4c5db/docs/MANAGED_FLEET_OPERATIONS.md).

## Development

    py -3 -m unittest discover -s tests -v
    py -3 skills\audit-venue-submission\scripts\package_integrity.py verify

See [PUBLISHING.md](PUBLISHING.md) for release gates,
[SECURITY.md](SECURITY.md) for trust boundaries, and
[CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes.

## Citation and license

See [CITATION.cff](CITATION.cff) and the [MIT License](LICENSE). Copies are
included in the installed skill package and tested against the repository-root
authorities.
