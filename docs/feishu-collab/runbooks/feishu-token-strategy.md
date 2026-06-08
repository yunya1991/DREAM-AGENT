# Feishu Token Strategy

## Purpose

Provide an operator-facing rulebook for choosing between `tenant_access_token` and `user_access_token`, storing the required credentials, and recovering when an API fails under the wrong identity.

## Identity Choice

- Use `tenant_access_token` when the API is designed for application identity, scheduled automation, or repository-owned bot execution.
- Use `user_access_token` when the API explicitly requires user identity, when the API documents OAuth user authorization, or when application identity fails even though the app permission is already enabled.
- If the API contract is unclear, try the documented default identity first, then switch identity based on the error message and scope model instead of repeatedly retrying the same token type.

## Practical Decision Rule

- Start with `tenant_access_token` for GitHub Actions jobs that write shared Base data or run unattended.
- Switch to `user_access_token` if the Feishu API documentation says the call uses user identity or if the permission belongs to a user-auth scope such as `approval:instance:read`.
- When switching to user identity, prefer `lark-cli --as user` in this repository because it already matches the working local verification path.

## Credential Storage

- Store application identity credentials in GitHub Secrets:
  - `LARK_APP_ID`
  - `LARK_APP_SECRET`
- Mint `tenant_access_token` at workflow runtime and export it through `GITHUB_ENV`; do not save the minted token back into the repository.
- If a workflow must use a durable user token, store it in GitHub Secrets rather than in tracked files.
- If user reauthorization is expected to rotate often, store only the OAuth method and operator steps in docs, and inject fresh `user_access_token` values only for the workflows that truly need them.

## User Token Flow

- Add the required redirect URL under the Feishu app security settings before requesting OAuth authorization.
- Request the exact user scopes needed for the API call.
- Exchange the authorization code for `user_access_token`.
- Use the resulting token through `lark-cli --as user` or an equivalent user-authenticated client path.
- If long-lived reuse is required, add `offline_access` and store the returned refresh credential in GitHub Secrets after the app permission is approved.

## Failure Recovery

- If a `tenant_access_token` call fails with a scope or identity mismatch, verify the API documentation before retrying.
- If a `user_access_token` call fails, confirm the user actually granted the scope during OAuth and re-run authorization if needed.
- If a direct HTTP call behaves differently from `lark-cli --as user`, prefer the CLI path first and treat raw HTTP as a second step after contract confirmation.

## Repository Conventions

- GitHub workflow bot jobs should inject:
  - `LARK_IDENTITY=bot`
  - `LARKSUITE_CLI_APP_ID=${{ secrets.LARK_APP_ID }}`
  - `LARKSUITE_CLI_TENANT_ACCESS_TOKEN=${{ env.LARK_TENANT_ACCESS_TOKEN }}`
  - `LARKSUITE_CLI_STRICT_MODE=off`
- User-identity recovery and verification steps should document:
  - the redirect URL
  - the requested scopes
  - the `lark-cli --as user` command used to verify success

## Current Known Example

- `approval-polling-writeback` uses bot identity for Base writeback inside GitHub Actions.
- `approval:instance:read` requires user identity verification in our live operator path.
- If app identity does not work, try user identity instead of continuing to debug the wrong token class.
