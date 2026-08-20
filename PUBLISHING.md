# Publishing

Owner: Ian-Tseng. Package: skills/audit-venue-submission/.

## Release gates

Before enabling managed repair, verify the policy/caller exact SHA agreement,
the `managed-repair-ready` label, required reviewers on both fixed protected
environments, explicit `OPENAI_API_KEY` passing, the Actions PR setting, and a
successful `workflow_dispatch` dry run. This repository is canary 2 and stays
disabled until canary 1 passes. A managed draft never authorizes evidence
acceptance, merge, release, publication, installed replacement, or activation.
Roll back policy and caller SHA together.

1. Confirm the worktree and reachable history contain no credentials,
   confidential manuscripts, reviewer material, or private machine paths.
2. Synchronize VERSION, root and packaged CITATION.cff,
   references/package-version.json, CHANGELOG.md, and the release tag.
3. Rebuild and verify the package manifest:

       py -3 skills\audit-venue-submission\scripts\package_integrity.py build --write
       py -3 skills\audit-venue-submission\scripts\package_integrity.py verify

4. Run the full suite and official validator:

       py -3 -m unittest discover -s tests -v
       py -3 <skill-creator-root>\scripts\quick_validate.py skills\audit-venue-submission

5. Review the diff, push a branch, open a version-prefixed PR, and require the
   exact PR head and merged main commit to pass all CI jobs.
6. Before publication, require an active no-bypass refs/tags/v* update and
   deletion ruleset and enable GitHub release immutability.
7. From exact merged main:

       gh skill publish .\skills --dry-run
       gh skill publish .\skills --tag v0.1.1
       gh release verify v0.1.1

8. In separate disposable homes and a neutral consumer directory, test public
   preview, Codex install/list/update, Claude Code install/list/update, package
   verification, cleanup, and fresh-client activation when each client exists.

Installation does not prove client discovery or invocation. Structural
validation does not prove venue compliance. If a post-publication defect is
found, increment the version; never rewrite the published tag.
