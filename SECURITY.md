# Security

Report vulnerabilities through GitHub private vulnerability reporting for
Ian-Tseng/audit-venue-submission. Do not publish exploit details,
confidential manuscripts, reviewer files, credentials, private paths, or portal
data in a public issue.

## Trust boundaries

- Manuscripts, DOCX/PDF files, archives, terminology contracts, and portal
  exports are untrusted input.
- Helpers are local collectors. They make no network requests and do not submit
  files.
- Confidential intake must establish authorization, current venue AI-policy
  review, permitted assistance, local-only processing, human accountability,
  conflicts handling, and retention before unpublished content is processed.
- Input and output paths must remain beneath the user-declared root.
- Archives are inspected without extraction and with entry/size bounds.
- Reports name secret categories without echoing secret values.
- Current official venue rules and live portal behavior remain external,
  time-sensitive evidence.

Only the latest release is supported. A security fix receives a new SemVer tag;
published tags are never moved.
