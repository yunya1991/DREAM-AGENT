# Node24 Main Merge Plan

1. Add a failing test or contract check for Node 24 opt-in coverage on the remaining workflows.
2. Update uncovered workflow files with `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true`.
3. Run targeted regression checks for workflow coverage and repository state.
4. Commit the workflow-only changes on the current branch and push.
5. Merge the branch into `main`, push `main`, and verify the branch tip is contained.
EOF; __tr_native_ec=$?; pwd -P >| '/var/folders/bq/2szq0m2s51s_mq6l3rywb50m0000gn/T/agent-toolhost/jobs/job-b5e1433a6b884f3f8c449f387e5a8132/cwd.txt'; exit "$__tr_native_ec"