---
name: record-terminal-demo
description: Use when recording a terminal demo of a CLI with VHS - writing or editing a .tape file, rendering a GIF or MP4, checking a recording is readable and free of secrets, or improving the styling of an existing demo for documentation, a README or social media.
---

# Record Terminal Demo

**Status:** experimental · **Risk:** approval-required

> Sample resource.
> [VHS's own documentation](https://github.com/charmbracelet/vhs) is
> authoritative wherever it disagrees with this file.

Record a short, deterministic terminal demo whose source stays in the repository
and can be re-rendered later. The `.tape` file is the artefact that matters; the
GIF is a build output.

## What this writes

This skill creates files in the user's working tree. Agree all three paths
before rendering:

- a `.tape` file, which is source and belongs in version control,
- any fixtures the tape needs,
- the rendered GIF, MP4 or WebM plus a contact sheet PNG, which are build
  outputs and are usually large.

Ask where generated media should go. Put it somewhere ignored by git unless the
user wants it tracked as a documentation asset, and confirm with
`git check-ignore -q <path>` rather than assuming. Never add a generated video
to a tracked `.gitignore` on the user's behalf without asking; use
`.git/info/exclude` if they want it ignored only locally.

## Workflow

1. Agree the one thing the recording should show. Cut every command that does
   not serve it.
2. Run the command sequence by hand first. VHS records whatever happens,
   including the failure.
3. Build or install the exact binary the demo will use, and say in the tape
   comments which build it was. A demo of a stale binary is worse than no demo.
4. Write the tape. Keep visible commands to what a real user would type; hide
   setup, `cd`, fixture preparation, aliases and clearing.
5. Render and verify with the bundled script, run from anywhere:

   ```bash
   python3 scripts/render_demo.py path/to/demo.tape
   ```

   It runs `vhs validate`, renders, fails on VHS's own `error:` lines, probes
   the artefact with `ffprobe` and writes a contact sheet.
6. Open the contact sheet with an image-viewing tool and look at it. Extract a
   full-resolution frame when colour, masking, alignment or spacing is in
   question.
7. Iterate. Most first takes are too long and have one unreadable colour.

## Styling

Start from these and change them only for a reason:

```text
Set Shell bash
Set FontSize 20
Set Width 1280
Set Height 720
Set Margin 0
Set Padding 28
Set LineHeight 1.15
Set TypingSpeed 30ms
Set Framerate 30
Set CursorBlink false
Set Theme "GitHub Dark"
```

- Match the theme to where the demo will be embedded. A dark theme suits most
  READMEs and social posts; check the contrast of the CLI's own ANSI colours
  against whichever you pick, because tool palettes are tuned for one background
  and fall apart on the other.
- Use a plain canvas with no window frame, title bar or outer margin, and keep
  the internal padding so text never touches the edge.
- Prefer `bash` for a predictable prompt.
- A leading newline in `PS1` separates prompt blocks without changing the
  spacing of ordinary output:

  ```bash
  export PS1="$(tput setaf 6)\n> $(tput sgr0)"
  ```

- In hidden setup, run `unset NO_COLOR` and set `TERM=xterm-256color` and
  `CLICOLOR=1`. Agent and CI environments often suppress colour, and a demo of a
  colourful CLI rendered in monochrome looks broken.
- Never pass a `--no-color` style flag to the command being demonstrated.
- Add short sleeps after meaningful output only, not after every command.
- Skip `--help`, install steps, title cards and commentary unless the user asked
  for them.

## Determinism

A demo re-rendered next month should look the same.

- Run the tape from its own directory. Resolve repository files with
  `git rev-parse --show-toplevel` rather than a chain of `../..`.
- Use `mktemp -d` for a disposable working directory and copy fixtures into it
  during hidden setup.
- Pin anything that varies: seeds, dates, sort order, table widths.
- If the tool colours output per worker or thread, force it single-threaded in
  hidden setup, for instance by wrapping the binary in a shell function, so the
  colours do not change between takes. Keep the visible command clean.
- Prefer flags that suppress timestamps or noisy logs only where they remove
  irrelevant output, never where they hide the behaviour being shown.

Example of a hidden setup block, with a placeholder tool:

```text
Hide
Type "export PATH=$(git rev-parse --show-toplevel)/bin:$PATH" Enter
Type "cd $(mktemp -d) && unset NO_COLOR && export TERM=xterm-256color" Enter
Type "clear" Enter
Show
Type "example-cli run ./pipeline --env dev" Enter
Sleep 4s
```

## Verification bar

Do not report the demo as done until every one of these holds:

- `vhs validate` passes.
- VHS exits successfully, emits no `error:` line and writes a non-empty file.
- `ffprobe` reports a plausible duration.
- The contact sheet has been looked at, not just generated.
- A full-resolution frame has been inspected when colour or legibility matters.
- Every command in the recording succeeded.
- No credential, token, real hostname, personal path or customer name is
  visible in any frame, including in scrollback and error output.
- Prompt spacing affects prompt blocks only.

Report the final artefact path, the tape path and the contact sheet path.

## Never

- Never put a real credential, token, internal hostname or production data in a
  tape or a fixture. Use obviously fake values.
- Never commit generated media without asking, and never edit a tracked
  `.gitignore` to hide it without asking.
- Never present a demo you have not looked at.
- Never record a command sequence you have not run successfully first.
