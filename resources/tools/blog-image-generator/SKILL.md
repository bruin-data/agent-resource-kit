---
name: blog-image-generator
description: Use when a blog post, changelog or landing page needs a cover image - searching Unsplash for a licence-friendly photo, cropping one to an exact aspect ratio, applying a pixelate, hue, duotone or dither treatment, or recording the photographer credit that Unsplash requires.
---

# Blog Image Generator

**Status:** experimental · **Risk:** approval-required

> Sample resource.
> [Unsplash's API guidelines and licence](https://unsplash.com/documentation)
> are authoritative wherever they disagree with this file.

`scripts/generate_blog_image.py` picks a photo from Unsplash or reads a local
file, crops it to an exact size and applies an optional treatment. It writes two
files: the image, and a `.source.json` beside it holding the photographer,
the photo URL and the attribution line.

## Before running anything

1. `pip install -r requirements.txt`. Pillow is the only dependency.
2. The access key comes from the `UNSPLASH_ACCESS_KEY` environment variable
   only. **Never ask the user to paste it into the chat and never put it in a
   command.** Tell them to register an application at
   https://unsplash.com/oauth/applications and export the Access Key themselves
   in a gitignored `.env` or `.envrc`. If the script says
   `UNSPLASH_ACCESS_KEY is not set`, relay that and stop; do not work around it.
3. **Agree the output path with the user before running.** This writes two files
   to disk and downloads from the network. `--output` is required and never
   guessed; the script refuses to overwrite an existing file unless `--force` is
   passed, and you should not pass `--force` without asking.
4. Ask which aspect ratio the destination needs. The default is 1600x900, which
   is 16:9. Do not assume it fits the user's layout.

## Choosing the photo

- Read the title and the argument of the piece, then choose a concrete visual
  idea. A photograph of a real object beats a literal screenshot or an abstract
  gradient.
- Query with a specific noun phrase: `stairs`, `server room cables`,
  `warehouse barcode scanner`. Omit `--query` for a random landscape photo.
- Avoid photographs with visible logos, brand marks or identifiable people for
  anything commercial. The Unsplash licence does not clear trademark, property
  or personality rights, and it cannot.
- Do not use Unsplash+ assets. They have separate terms.

## Running it

```bash
python3 scripts/generate_blog_image.py \
  --query "stairs" \
  --output ./covers/data-pipeline-stairs.webp

# a specific ratio and crop placement
python3 scripts/generate_blog_image.py \
  --query "warehouse shelves" \
  --output ./covers/inventory.webp \
  --width 1920 --height 1080 --focal top

# treatments, applied in this order: distort, pixelate, hue, duotone, dither
python3 scripts/generate_blog_image.py \
  --query "street at night" \
  --output ./covers/city.webp \
  --distort --pixelate 3 --dither --tint "#2b6cb0" --cell 2

# no key needed: treat an image you already have
python3 scripts/generate_blog_image.py \
  --input ./photos/original.jpg \
  --output ./covers/treated.webp \
  --duotone --tint "#334155"
```

Pass `--tint` the accent colour of the site the image is going on. Set
`--app-name` to the Unsplash application name the key belongs to, because it
goes into the `utm_source` of the credit links.

## After running it

1. Open the image and look at it. Cropping to a fixed ratio routinely cuts the
   subject in half; re-run with a different `--focal`, query or size if it does.
2. Read the `.source.json`. It holds the attribution line and the credit links.
3. **Publish the credit.** Unsplash asks for "Photo by NAME on Unsplash" with
   links back to the photographer and to Unsplash. Put it wherever the site
   shows image credits, and keep the JSON in version control beside the image so
   the source stays recoverable.
4. Only then reference the image from the page or post frontmatter.

## Never

- Never ask for, accept, print or log the access key, and never add a flag that
  takes one. If the user pastes one, tell them not to and to rotate it.
- Never commit the key or write it into any file in the repository.
- Never overwrite an existing cover without the user asking for it.
- Never publish an Unsplash photo without the photographer credit.
- Never use a photo containing a logo, a trademark or an identifiable face for
  commercial material without checking the rights separately.
- Never claim the licence covers something it does not. It grants use of the
  photograph, not of what the photograph depicts.
