# Migration handoff

## Purpose and current status

This repository publishes the Roth Estate-Growth Desk at `roth.aipeterlab.com`. It applies public market data and upstream QQQ strategy signals to a documented long-horizon allocation while deliberately avoiding private brokerage integrations. At the September 8, 2026 migration audit, `main` began clean and synchronized with `origin/main`.

## Structure and design

- `index.html`: static dashboard UI.
- `data/dashboard.json`: generated dashboard state consumed by the UI.
- `scripts/update_dashboard.py`: Python 3.12 standard-library updater.
- `.github/workflows/daily-update.yml`: manual workflow dispatch that runs the updater and commits only `data/dashboard.json`.
- `_headers`: hosting headers.
- `README.md`: short public project description.
- `AGENTS.md`: durable Codex rules.

The updater obtains market prices from Yahoo Finance's chart endpoint and QQQ strategy data from the AIPeterLab QQQ/QLD signal repository. Strategy output is cross-checked before JSON is written. Private brokerage balances must remain out of public integrations and output.

## Recreate and operate

Requirements: Git, Python 3.12, and outbound HTTPS access. There are no third-party Python packages, Node dependencies, database, or local build step.

```powershell
python scripts/update_dashboard.py
python -m py_compile scripts/update_dashboard.py
```

Optional environment-variable override names (never commit their values):

- `QQQ_SIGNALS_URL`
- `MAX_QQQ_SIGNAL_AGE_HOURS`

External services: GitHub repository `AIPeterLab/roth-estate-growth-desk`, GitHub Actions with `contents: write`, upstream raw GitHub signal data, Yahoo Finance market data, and Cloudflare hosting/custom domain configuration.

## Source knowledge and account-owned state

The original Windows workspace contained `C:\Users\Ella\Documents\401K Desk\Roth guide.docx`, `Roth-guide-copy.zip`, and extracted `Roth-guide-xml/` outside this Git repository. They may contain private financial information, so keep them in a separate private backup unless explicitly approved for version control. Cloudflare project/domain settings, GitHub authorization, workflow permissions, and login sessions are also external to Git.

## Unfinished work, risks, and next steps

- There is no formal automated test suite; syntax-check the updater, run it with network access, and inspect the generated JSON/UI after changes.
- Upstream URLs and Yahoo Finance are availability dependencies.
- After migration, verify the GitHub workflow can commit, Cloudflare still deploys `main`, and the custom domain resolves.
- Read `AGENTS.md` before continuing development.
