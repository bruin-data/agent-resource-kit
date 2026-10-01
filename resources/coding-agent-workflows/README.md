# Coding agent workflows

Repeatable workflows for agents working on a codebase: release notes, demos, and
the routine jobs that benefit from being written down once.

| Resource | Risk | Use it when |
|---|---|---|
| [`generate-changelog`](generate-changelog/) | read-only | You need customer-facing release notes built from git history across one or more repos |
| [`record-terminal-demo`](record-terminal-demo/) | approval-required | You want a terminal demo of a CLI recorded with VHS, rendered and checked before anyone sees it |

Both are stack-agnostic. Neither assumes a language, framework or CI system.
`record-terminal-demo` is the only one that ships code; it needs `vhs` and
`ffmpeg` installed, and its README says how.

## Related, maintained elsewhere

Some things are better pointed at than vendored. [`humanizer`](https://github.com/blader/humanizer)
strips the tells of AI-written prose and is maintained as its own MIT project.
Install it from there rather than expecting a copy here, which would fork on the
first upstream change.
