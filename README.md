# Workflow Commons

## Python Test Workflow (pythonapp.yml)
This repository provides a reusable workflow for running Python tests and generating a coverage badge.

**Workflow Files**

- `test.sh` the workflow downloads and runs a shared test.sh script, so you do not need to maintain a custom one in each repository.

- `docker-compose.yml` provide required services (MongoDB, Memcached, LMS, CMS, etc). Your repository is mounted at /openedx/requirements/app inside the container.

**Prerequisites**

- `test_requirements.txt` should be present at the project root. List extra dependencies needed for testing. These will be installed before running tests.

- `setup.cfg` should exist at the project root. Used to configure test settings, pytest options and coverage rules. The workflow uses this file for the test environment to ensure consistent configuration.

**Usage**
Call this workflow from your repository using workflow_call. Example:
```
jobs:
  build:
    uses: eol-uchile/workflow-commons/.github/workflows/pythonapp.yml@main
    with:
      app_id: ${{ vars.EOLITO_BOT_APP_ID }}
      django-lms: true
      django-cms: false
      platform-eol: true
      platform-openuchile: false
    secrets:
      private_key: ${{ secrets.EOLITO_BOT_PRIVATE_KEY }}
```
- `django-lms` (boolean) enables tests for the Django LMS
- `django-cms` (boolean) enables tests for the Django CMS
- `platform-eol` (boolean) enables testing over the platform's EOL build
- `platform-openuchile` (boolean) enables testing over the platform's Open UChile build
- `app_id` (variable) GitHub App ID used by the workflow for authenticated operations.
- `private_key` (secret) Private key corresponding to the GitHub App, used for authentication.

*The `vars.EOLITO_BOT_APP_ID` and `secrets.EOLITO_BOT_PRIVATE_KEY` are inherited from the org.*

**Local run with ACT**
ACT allows you to run the workflow locally for development and debugging purposes.
To use it, run the following command from each Pythonapp repository:

`act -W .github/workflows/pythonapp.yml --bind`

- `-W .github/workflows/pythonapp.yml` specifies the workflow file to trigger.
- `--bind` mounts the current directory into the container so the workflow can run `docker compose` against your code — it also causes file changes (for example `coverage-badge.svg`) to be written back to your working tree.

The commit step is skipped locally thanks to `if: ${{ !env.ACT }}` — this prevents local runs from pushing commits or dirtying branches. This setup is meant only to test and debug workflows locally, not to generate or push badges. Although it is not required, if you want to push the badge, just commit it manually after running act.

## Pending Verifications Cronjob (verifications_cronjob.yml)

This repository provides a tiny Python bot that fetches pending verifications from a Metabase endpoint, renders a table image, and posts it to a Discord channel via webhook. Intended to run daily from GitHub Actions

Four repository secrets are needed:

* `METABASE_AUTH_STRING` (Metabase Basic auth string, already base64)
* `METABASE_API_KEY` (Metabase REST API key)
* `METABASE_URL` (HTTP(S) endpoint to the query)
* `DISCORD_WEBHOOK_URL` (Discord webhook URL)
