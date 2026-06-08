---
name: "okr-driven"
description: "Compiles spec + plan into Objective/KR, Base, task, and workflow execution previews, then executes after confirmation. Invoke when building or advancing goal-driven delivery from approved spec and plan."
---

# OKR-driven

## When to use

Use this skill when:

- the user already has an approved `spec + plan`
- the user wants to turn them into `OKR + Base + task + workflow`
- the user wants a preview before any online writes
- the user wants post-run projection refresh and boss-view verification

Do not use this skill when:

- only a raw idea exists and brainstorming is still needed
- there is no usable spec or implementation plan yet
- the request is only to write KR wording without execution

## Required execution mode

This skill always runs in two stages:

1. preview
2. confirmation
3. execution
4. projection refresh
5. boss-view verification
6. handoff generation

Never skip the preview step.

## Inputs

- approved spec path
- approved implementation plan path
- optional live identifiers already known from previous runs

## Stage 1: Build preview

Run:

```bash
python3 github-actions/build_okr_driven_preview.py <<'EOF'
{
  "spec_text": "...",
  "plan_text": "..."
}
EOF
```

Then materialize:

```bash
python3 github-actions/materialize_okr_driven_execution.py <<'EOF'
{ ...preview json... }
EOF
```

Present:

- objects to create
- objects to update
- anchor changes
- execution order
- risk flags

## Stage 2: Execute after confirmation

Execution order:

1. OKR
2. Base
3. task
4. workflow
5. projection refresh
6. boss-view verification

Keep IDs as strings at every step.

## Projection refresh

After online writes complete, run:

```bash
python3 github-actions/refresh_okr_driven_goal_projection.py <<'EOF'
{
  "goal": { ... },
  "tasks": [ ... ]
}
EOF
```

Then write the refreshed payload back to Base and re-read the boss view.

## Verification

Always verify:

- real objective id
- real record id
- workflow_signal
- boss view visible fields
- handoff output
