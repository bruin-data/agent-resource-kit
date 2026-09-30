---
name: staged-writing
description: Use when someone wants to write a post, newsletter, blog, thread or docs page in their own words and wants an agent to outline it, then proofread, fact-check and tighten the structure between their drafts. Use when the request is help writing, not a draft written for them.
---

# Staged writing

**Status:** experimental · **Risk:** read-only

> This is a writing method, not a tool
> wrapper, so it has no upstream documentation to defer to. Where it conflicts
> with the writer's own conventions or house style, their conventions win.

The writer writes the prose. You outline, check and tidy. That division is the
whole point of this skill: a piece drafted by an agent and edited by a human
reads like an agent wrote it, because one did. If you produce the paragraphs,
you have defeated the skill. Do not do it.

Works for long-form posts, newsletters, short social posts, blogs and
documentation. Keep to one channel at a time.

## Ground the brief

Before outlining, establish from the request:

- Channel, audience, topic, core argument, target length.
- Sources, constraints, and any deadline or house style.
- A voice reference, if the writer has one: a sample of their past writing, a
  style guide, or a short list of rules. If they offer none, work without one
  and do not invent a voice for them.

Resolve what the sources already answer before asking the writer for it. Use
primary documentation for technical claims and code. Never guess syntax.

Unless told otherwise: keep the idea central, use any product or tool only as a
supporting example, hold code to one short verified snippet, and avoid
promotional framing and unsupported claims.

## The stages

Each stage ends at a gate. Do not cross a gate on your own. Stop, say what you
need, and wait.

### Stage 1: outline only

Produce a working document containing:

- A header: channel, audience, core argument, target word count, status.
- One labelled section per intended paragraph.
- Two to four TODO bullets under each label, each 5 to 10 words.
- A blank `<!-- write paragraph here -->` marker after each section.
- The verified code snippet in position, if the piece needs one.

Each bullet says what the paragraph must achieve. None of them is a sentence of
the finished piece. Then stop.

**Gate: the writer writes.** Do not fill a marker, not even as an example, not
even if asked to "just show what you mean". If pushed, offer a sharper bullet
instead.

### Stage 2: receive the draft

Accept one paragraph, several, or a whole updated file. Leave unwritten
sections blank. If an ambiguity would change the meaning of the piece, flag it
in one line. Otherwise say nothing and move on.

### Stage 3: proofread, nothing else

Correct only grammar, spelling, punctuation and obvious typos.

Preserve wording, paragraph order, rhythm, argument, technical meaning and
deliberate informality. Do not improve a transition, reorder an idea, add an
example, cut a repetition or smooth a sentence you find clumsy. Those are
Stage 6, and only if asked.

Return the proofread text and list any correction that could change meaning.

### Stage 4: fact-check and technical review

On the proofread version, check every material:

- Factual claim, number, date, comparison and described behaviour.
- Concept, and the relationship asserted between concepts.
- Technical term, acronym and definition.
- Code snippet, command, configuration and stated output.

For each check, use current primary sources: official documentation,
specifications, source repositories, original research. Run code only when it
is safe and the writer has agreed; never describe unexecuted code as tested.

Correct objective errors in place, changing as few words as possible. Separate
verifiable facts from the writer's opinions, interpretations and personal
experience, and leave the latter alone. Where sources conflict or you could not
verify something, name the exact claim and say so. Qualify or drop it rather
than guessing.

Deliver a short review note: each material correction, why, and the source.
If nothing needed changing, say the pass found no issues. Then stop.

**Gate: the writer revises.**

### Stage 5: take their revision as truth

Their next version supersedes yours. Do not reinstate wording they removed, and
do not re-raise a correction they considered and rejected. Wait until they
explicitly ask for the structural pass.

### Stage 6: flow and structure

Only on request, and only now. Review for:

- Narrative progression and paragraph order.
- Transitions, repetition and detours.
- Consistency between hook, example, argument and ending.
- Channel fit, length and the agreed balance of idea to product.

Make the fewest changes that achieve cohesion. Preserve their ideas and their
voice. Invent no experiences, examples, facts or opinions.

Then re-check every sentence whose meaning or terminology changed in this pass,
because structural edits cause technical drift. Fix the drift before returning
the piece.

Optionally, a separate humanizer skill exists publicly at
https://github.com/blader/humanizer and can be run at this stage to strip
AI-ish patterns. This workflow does not require it and does not depend on it.
If it is not installed, finish the stage without it.

## Adapting to another channel

Only after the writer approves the source version. Build a fresh outline for
the new channel, then repeat Stages 2 to 6. Preserve the central argument and
the verified facts. Expand reasoning for long-form, distil hard for short
social. Do not simply trim the previous version.

## Never

- **Never write the prose.** Not a sample paragraph, not a "rough version to
  react to", not a rewritten sentence during proofreading. If the writer
  genuinely wants a draft written for them, that is a different job: say so
  plainly and get an explicit instruction before you start.
- **Never quietly change their voice.** Every edit beyond a typo is visible and
  attributed to a stage. Their odd phrasing is usually a choice.
- **Never invent a citation, source, statistic or quotation.** An unverifiable
  claim gets flagged, not sourced by guesswork.
- **Never assert a fact you did not check.** Say "unverified" and name the gap.
- **Never skip a gate**, combine stages, or run the structural pass because the
  piece would obviously be better for it.
- **Never publish or send anything.** Producing the text is the end of the job.

## Before returning at any stage

- The writer is still the author of every sentence they asked to write.
- Every outline bullet is 5 to 10 words and none is finished prose.
- Claims, terms and code match authoritative sources, or are flagged.
- Corrections carry a reason and a source.
- Only the requested channel's artefact was created or edited.
- The work is paused at the correct gate, and you have said which one.
