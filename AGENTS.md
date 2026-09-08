# Codex operating instructions

- Read `README.md` and `MIGRATION_HANDOFF.md` before changing this repository.
- Preserve the rule that private brokerage balances are not fetched or published.
- Treat `data/dashboard.json` as generated output from `scripts/update_dashboard.py`; update it through the script when practical.
- Keep the updater compatible with Python 3.12 and the standard library unless a dependency is explicitly documented.
- Never commit environment files, credentials, tokens, private keys, Wrangler state, or private source documents.
- Validate Python syntax, run the updater when network access is available, and review generated-data diffs before committing.
