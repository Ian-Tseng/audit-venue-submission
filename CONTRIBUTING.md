# Contributing

Keep changes evidence-bounded and portable.

1. Open an issue describing the violated contract or missing venue-neutral
   capability. Do not place confidential manuscripts, reviews, credentials, or
   security details in a public issue.
2. Add a deterministic regression test before changing a helper.
3. Preserve the separation between stable venue-neutral guidance and mutable
   venue/year/track rules.
4. Run the complete test suite, package verifier, official skill validator, and
   secret/private-path scan.
5. Update VERSION, both citation files, package version, manifest, and
   changelog together for a release.

Security issues belong in GitHub private vulnerability reporting as described
in [SECURITY.md](SECURITY.md).
