# Node24 Main Merge Design

## Goal

- Merge the validated `pilot/acceptance-orchestration-v2-e2e-20260607` branch back into `main`.
- Remove current GitHub Actions Node 24 deprecation warnings by applying the repository's existing opt-in pattern.

## Approved Approach

- Use the existing repository convention: add `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` at the workflow top level for every workflow that still uses JavaScript actions without the opt-in.
- Avoid broad behavior changes such as action major-version upgrades in this pass.
- Validate the workflow set with targeted checks, then merge to `main` and push.

## Scope

- Update only `.github/workflows/*.yml` files that still rely on `actions/checkout@v4` or `actions/upload-artifact@v4` and do not already opt into Node 24.
- Do not change workflow business logic, inputs, or secrets handling.
- Merge `pilot/acceptance-orchestration-v2-e2e-20260607` into `main` after the workflow changes are committed and verified.

## Verification

- Confirm every relevant workflow either already has or now includes `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true`.
- Re-run focused workflow presence checks if present; otherwise use repository grep validation.
- Confirm `main` contains the new commit and push succeeds.
