# blog-image-generator

A small script that turns a photograph into a finished cover image. It selects a
photo from [Unsplash](https://unsplash.com) by search term or at random, or
reads one you already have, crops it to an exact size and applies an optional
treatment: scanline distortion, pixelation, hue rotation, duotone, ordered
dither. Every Unsplash run writes a sidecar JSON file with the photographer and
the attribution line, and pings Unsplash's download tracking endpoint.

> **Example code, provided as-is.** This is not part of the Bruin platform and
> is not a supported Bruin product. It is a sample you configure, review and run
> yourself with your own credentials. No support agreement or SLA covers it. See
> the repository [LICENSE](../../../LICENSE) for the warranty disclaimer.

Unsplash's own documentation is authoritative. Their API, licence and
attribution requirements change without notice; check
[unsplash.com/documentation](https://unsplash.com/documentation) and
[unsplash.com/license](https://unsplash.com/license) before you publish.

## Install

Python 3.9 or newer.

```bash
cd blog-image-generator
pip install -r requirements.txt
python3 scripts/generate_blog_image.py --help
```

Pillow is the only dependency, and 10.0 or newer is required. Everything else,
including the HTTP calls, is standard library.

**System dependencies: none.** No ImageMagick, no ffmpeg. Pillow ships its own
binary wheels, including WebP support. If you built Pillow from source without
WebP, write a `.jpg` or `.png` output instead.

## Get an Unsplash access key

Register an application at
[unsplash.com/oauth/applications](https://unsplash.com/oauth/applications) and
copy its **Access Key** (not the secret key). A demo application is rate limited
to 50 requests an hour, which is ample here; production access needs Unsplash's
approval and compliance with their API guidelines.

Each generated image costs two API calls: one to select the photo, one to record
the download.

## Set the environment variable

The key is read from `UNSPLASH_ACCESS_KEY` and from nowhere else. There is no
flag and no config file for it, deliberately: a flag lands in your shell history
and in the process list.

```bash
export UNSPLASH_ACCESS_KEY='...'        # current shell only
```

For something persistent use a file your shell loads and git ignores, such as
`.envrc` with [direnv](https://direnv.net), a `.env`, or your password manager's
CLI. Add the file to `.gitignore` **before** you write the key into it. If a key
is committed or pasted into a chat, revoke it in Unsplash and issue a new one.

No key is needed for `--input`, which processes a local image.

## Usage

```bash
# search a concept, write a 16:9 cover
python3 scripts/generate_blog_image.py \
  --query "stairs" --output ./covers/stairs.webp

# a random landscape photo at a different size and crop
python3 scripts/generate_blog_image.py \
  --output ./covers/random.webp --width 1920 --height 1080 --focal top

# treat a local image, no key required
python3 scripts/generate_blog_image.py \
  --input ./photos/original.jpg --output ./covers/treated.webp \
  --duotone --tint "#334155"
```

`--output` is required, extension included; the format follows the extension.
An existing file is never overwritten without `--force`.

Treatments are independent flags applied in a fixed order:

| Flag | Effect |
|---|---|
| `--distort` | Subtle horizontal scanline wave |
| `--pixelate BLOCK` | Square blocks, 2 pixels or more |
| `--hue DEGREES` | Global hue rotation |
| `--duotone` | Luminance mapped onto a dark-to-`--tint` ramp |
| `--dither --cell N` | Ordered dither mesh in `--tint` over the duotone base |

`--tint` defaults to a neutral grey, which gives a monochrome duotone. Pass your
own accent colour as hex. Combining `--distort --pixelate 3 --dither` gives the
heavily textured look where the photograph survives only as a silhouette.

## Attribution and licence

The [Unsplash License](https://unsplash.com/license) allows free commercial and
non-commercial use, with modification, without asking permission. It does not
allow selling unmodified copies, and it does not allow building a competing
service from Unsplash photos.

Two things it does **not** give you, and this matters:

- **It does not clear what is in the photograph.** Trademarks, logos, buildings,
  artwork and recognisable people carry their own rights. For commercial
  material, prefer photographs without them.
- **It does not remove the credit expectation.** Unsplash asks for
  "Photo by NAME on Unsplash" with links to the photographer and to Unsplash,
  and their API guidelines require both those links to carry your application's
  `utm_source`. This script builds those links for you, using `--app-name`. Set
  it to the name of the application your key belongs to.

Every Unsplash run writes `<output>.source.json` beside the image:

```json
{
  "provider": "unsplash",
  "license": "Unsplash License, https://unsplash.com/license",
  "photographer": "A Photographer",
  "photographer_url": "https://unsplash.com/@someone?utm_source=...",
  "photo_url": "https://unsplash.com/photos/...?utm_source=...",
  "attribution": "Photo by A Photographer on Unsplash"
}
```

Keep that file with the image in version control. Without it the source becomes
unrecoverable, and an image whose provenance nobody can prove is a liability.

The script also calls the download tracking endpoint on every selection, which
Unsplash's API guidelines require. Do not remove that call.

## Limitations

- **No approval prompt.** The script writes the files it is told to write. The
  guard rails are that `--output` is mandatory and `--force` is needed to
  overwrite. If you drive it from an agent, the agent owns the confirmation.
- **Crops are blind.** `ImageOps.fit` centres on the focal point you name; it
  does not detect faces or subjects. Look at the result.
- **Random selection is random.** The same query returns a different photo each
  run. There is no way to re-fetch a previous choice except through the photo ID
  in the sidecar JSON.
- **No caching, retries or rate-limit backoff.** An HTTP error surfaces as an
  error. A demo key gives 50 requests an hour, and each image costs two.
- **`--dither` is a Python pixel loop.** It is fine at cover size and slow at
  several thousand pixels wide.
- **`--input` metadata is a stub.** For a local file the script records the path
  and nothing else. Whether you may publish it is your problem to establish.
- **Unverified against a live key.** The Unsplash request shapes came from their
  documentation. Check the first response you get.
