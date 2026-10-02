## What this changes

One or two sentences.

## Verification

```bash
./tests/check.py
```

- [ ] Checks pass
- [ ] Documented behaviour is behaviour I observed, not behaviour I expected
- [ ] Upstream note carries the version and date I checked against

## For a new resource

- [ ] `name` matches the folder, `description` starts with `Use when`
- [ ] `**Status:**` and `**Risk:**` line, chosen conservatively
- [ ] Listed in the root `README.md` index and in `.claude-plugin/marketplace.json`
- [ ] Says what the tool cannot do, and what the user has to decide
- [ ] No credentials, customer data or production output
- [ ] Does not ask a user to paste a credential into a conversation
- [ ] Does not modify global agent, editor or MCP settings

## What you could not test

Genuinely useful. Silence gets a resource merged with a wrong claim in it.
