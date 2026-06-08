# Execution Checklist

## Intake Gate

- Confirm `asset_type` is present
- Confirm title is present
- Confirm source skill or handoff context is visible

## Validation Gate

- Confirm target path is resolved
- Confirm template type matches asset type
- Confirm evidence refs are present
- Confirm overwrite handling is explicit

## Check Gate

- Confirm drift results are visible
- Confirm gap results are visible
- Confirm stale results are visible

## Verification Gate

- Confirm target file exists
- Confirm index alignment is checked
- Confirm handoff and `KnowledgeUpdate` receipt are emitted
