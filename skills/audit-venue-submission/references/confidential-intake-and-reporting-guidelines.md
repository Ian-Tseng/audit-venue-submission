# Confidential Intake and Reporting-Guideline Coverage

## Intake boundary

Create one local intake record before reading unpublished or restricted
submission content. Processing is blocked unless the requester is authorized,
the applicable confidentiality and venue AI policies were checked, AI
assistance is permitted, external processing is disabled, a human remains
accountable, conflicts are resolved or absent, and retention is decided.

The intake record contains administrative labels and evidence locators, not
manuscript or reviewer prose. Keep it inside the authorized project boundary;
never add a confidential instance to this reusable package. The helper accepts
one ordinary UTF-8 JSON file up to 128 KiB and rejects linked/reparse inputs.

## Non-scoring guideline selection

```text
<python-3> "<skill-root>/scripts/submission_intake.py" guidelines --study-design <design>
<python-3> "<skill-root>/scripts/submission_intake.py" validate --intake <local-intake.json>
```

The selector maps a declared design to candidate main guidelines such as
CONSORT, STROBE, PRISMA, SPIRIT, PRISMA-P, STARD, TRIPOD, CARE, SRQR/COREQ,
ARRIVE, SQUIRE, or CHEERS. It does not decide whether a design label is
scientifically correct, select specialized extensions, reproduce a checklist,
or score compliance.

For every candidate:

1. open the current official guideline or EQUATOR record;
2. confirm version, extensions, article type, venue mandate, and required
   checklist/flow-diagram upload;
3. record `applicable`, `not_applicable`, or `pending`, a local evidence
   locator, and the human verifier;
4. audit the actual checklist items outside this selector;
5. keep unresolved applicability as `PARTIAL` or `PENDING`, never `PASS`.

## Source record

Checked **2026-08-27 (Asia/Taipei)**. EQUATOR describes reporting guidelines as
structured tools for reporting specific research types and lists main
study-design mappings:

- [EQUATOR reporting-guideline search](https://www.equator-network.org/reporting-guidelines/)
- [EQUATOR definition](https://www.equator-network.org/about-us/what-is-a-reporting-guideline/)
- [EQUATOR experimental studies](https://www.equator-network.org/reporting-guidelines-study-design/experimental-studies/)
- [EQUATOR STROBE record](https://www.equator-network.org/reporting-guidelines/strobe/)

These links support candidate discovery only. The live official guideline,
venue instructions, and portal remain time-sensitive authorities.
