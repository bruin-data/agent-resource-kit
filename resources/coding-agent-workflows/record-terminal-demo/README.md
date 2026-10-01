# record-terminal-demo

A skill and one helper script for recording terminal demos of any CLI with
[VHS](https://github.com/charmbracelet/vhs). You write a `.tape` file; VHS types
the commands into a real terminal and renders a GIF, MP4 or WebM. The script
wraps that with the verification step people skip: validate, render, check VHS
did not fail quietly, probe the artefact, and build a contact sheet you can
actually look at.

> **Example code, provided as-is.** This is not part of the Bruin platform and
> is not a supported Bruin product. It is a sample you review and run yourself.
> No support agreement or SLA covers it. See the repository
> [LICENSE](../../../LICENSE) for the warranty disclaimer.

VHS's own documentation is authoritative. Tape syntax, themes and `Set` options
change; check upstream before trusting a directive named here.

## System dependencies

These are not Python packages. Install them first.

| Tool | Why |
|---|---|
| `vhs` | Renders the tape |
| `ttyd` | VHS drives it to get a real terminal. Required by VHS itself |
| `ffmpeg` | VHS encodes with it; the script also builds the contact sheet with it |
| `ffprobe` | Ships with ffmpeg. Used to check the artefact is not truncated |

macOS:

```bash
brew install vhs ffmpeg
```

Homebrew pulls in `ttyd` as a VHS dependency.

Debian or Ubuntu:

```bash
sudo apt install ffmpeg
# vhs and ttyd: see the install instructions at
# https://github.com/charmbracelet/vhs#installation
```

With Go already installed:

```bash
go install github.com/charmbracelet/vhs@latest
```

Check what you have:

```bash
vhs --version && ffmpeg -version | head -1 && ffprobe -version | head -1
```

## Python dependencies

None. `scripts/render_demo.py` is standard library only and needs Python 3.9 or
newer. `requirements.txt` exists to say exactly that.

## Credentials

None. Nothing here talks to a network service.

Be careful about the opposite direction: a terminal recording captures whatever
is on screen, including an API key echoed by a command, a token in an error
message, a real hostname or a customer name. Use fake values in tapes and
fixtures, and look at every frame before publishing.

## Usage

Write a tape, then render it:

```bash
python3 scripts/render_demo.py path/to/demo.tape
```

The script:

1. runs `vhs validate`,
2. creates the directory each `Output` names,
3. renders from the tape's own directory, because VHS resolves `Output` paths
   relative to its working directory,
4. fails if VHS printed an `error:` line, which some versions do while still
   exiting 0 after writing a partial video,
5. runs `ffprobe` and rejects a zero-length or zero-duration artefact,
6. writes a six-frame contact sheet PNG beside the media, or wherever
   `--qa-dir` points.

Options:

```
--qa-dir DIR          where contact sheets go. Default: beside the media
--no-contact-sheet    skip the sheet, and the ffmpeg requirement with it
--no-probe            skip the duration check. Implies --no-contact-sheet
```

A minimal tape to start from:

```text
Output demo.gif

Set Shell bash
Set FontSize 20
Set Width 1280
Set Height 720
Set Padding 28
Set TypingSpeed 30ms
Set Theme "GitHub Dark"

Hide
Type "cd $(mktemp -d) && unset NO_COLOR && export TERM=xterm-256color" Enter
Type "clear" Enter
Show

Type "example-cli run ./pipeline" Enter
Sleep 4s
```

## What it writes

`.tape` files and fixtures you author, plus the rendered media and contact
sheets, all in your working tree. Rendered media is large and regenerable;
ignore it in git unless you deliberately want it tracked as a documentation
asset. The script never touches `.gitignore` or commits anything.

## Limitations

- **The contact sheet is a sample, not a review.** Six frames spread across the
  duration will miss a one-second glitch. Watch the video before publishing
  anything customer-facing.
- **No rendering happens without a working `vhs`**, and VHS needs a real
  terminal emulator via `ttyd`. Headless containers often lack it.
- **`Output` parsing is deliberately simple.** The script reads `Output`
  directives with `shlex` and does not evaluate anything else in the tape, so a
  path built from a shell variable will not be understood.
- **No secret scanning.** Nothing here inspects frames for credentials. That is
  your eyes, and the rule to use fake values in the first place.
- **Timing is not asserted.** A demo can pass every check here and still be
  forty seconds of dead air. Judge the pacing yourself.
