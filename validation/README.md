# Validation Authority

This directory contains the local release-candidate evidence for
Audit Venue Submission 0.2.0.

- [`release-candidate-test-receipt.json`](release-candidate-test-receipt.json)
  records 33 passing local tests, package verification, official skill
  validation, an outbound-free publisher dry-run, and explicit external limits.
- [`component-map/accepted-map.json`](component-map/accepted-map.json) is the
  exact owner-accepted map `component-map-2761aab791f3` with SHA-256
  `7d933fa3899303524397d0bdb75eb642492afbac209901f81e403969aa3ae956`.
- [`history/20260827T052058098897Z-19371ac5.json`](history/20260827T052058098897Z-19371ac5.json)
  is the current append-only semantic authority with canonical digest
  `7b517f0d67a512d3c4962f7888f85d4f68b72f5520669d41f8214c130e2f705e`.
- [`reports/20260827T052058098897Z-19371ac5.md`](reports/20260827T052058098897Z-19371ac5.md)
  is its deterministic human-readable view.

Earlier map events remain immutable historical states. The current record is
`PARTIAL`: local structural checks do not establish PR or merged-main CI,
tag protection, immutable publication, public install/update, fresh client
activation, venue compliance, or scientific validity for any submission.
