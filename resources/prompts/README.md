# Prompts

Reusable prompts and staged workflows for tasks where the sequence matters more
than the tooling.

| Resource | Risk | Use it when |
|---|---|---|
| [`staged-writing`](staged-writing/) | read-only | Writing a post, newsletter or doc where you want the agent to outline, proofread and fact-check, but not to write the prose |

## What makes one worth keeping

- **It works for a class of tasks**, not one request that happened to go well.
- **It is short enough to be read.** Past roughly 500 words people and agents
  both skim.
- **It says what the agent must not do.** For most prompts here that is the
  load-bearing half.
- **It has an expected shape of output**, even when the exact words vary.

A prompt cannot enforce anything. Where behaviour actually matters, the control
belongs in a permission setting or a scoped credential, and the prompt should say
so rather than implying otherwise.
