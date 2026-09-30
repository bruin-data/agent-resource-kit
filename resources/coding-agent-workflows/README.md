# Coding agent workflows

Repeatable workflows for agents working on a codebase: review, release, and the
routine jobs that benefit from being written down once.

| Resource | Risk | Use it when |
|---|---|---|
| [`ultra-review`](ultra-review/) | read-only | You want a deliberately harsh maintainability review of a branch: abstraction quality, giant files, spaghetti conditions |
| [`generate-changelog`](generate-changelog/) | read-only | You need customer-facing release notes built from git history across one or more repos |
| [`record-terminal-demo`](record-terminal-demo/) | approval-required | You want a terminal demo of a CLI recorded with VHS, rendered and checked before anyone sees it |

All three are stack-agnostic. None assumes a language, framework or CI system.
`record-terminal-demo` is the only one that ships code and the only one
that writes files into your working tree; it needs `vhs` and `ffmpeg`
installed, and its README says how.

`ultra-review` is the most opinionated of the three. It pushes a reviewer to be
ambitious about structure rather than listing local nits, which is the failure
mode of most automated review. Expect it to propose restructuring, and expect to
decline some of what it proposes.

## Related, maintained elsewhere

Some things are better pointed at than vendored. [`humanizer`](https://github.com/blader/humanizer)
strips the tells of AI-written prose and is maintained as its own MIT project.
Install it from there rather than expecting a copy here, which would fork on the
first upstream change.
