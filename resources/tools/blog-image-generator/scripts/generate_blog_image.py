#!/usr/bin/env python3
"""Select, crop and treat a cover image from Unsplash or a local file.

Sample code: read it before you run it.

Design rules this file follows:

* The Unsplash access key is read from the ``UNSPLASH_ACCESS_KEY`` environment
  variable and from nowhere else. There is no flag and no config file, so the
  key cannot end up in shell history, a process list or a commit.
* The key is never printed, including in an error body echoed back by Unsplash.
* The output path is always explicit. ``--output`` is required, and an existing
  file is never overwritten without ``--force``.
* Every Unsplash download writes a sidecar JSON file with the photographer,
  the photo URL and an attribution line, and pings Unsplash's download
  tracking endpoint, both of which their API guidelines require.

Written against the Unsplash API v1 as documented at https://unsplash.com/documentation
and Pillow 10. Requires Python 3.9 or newer.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

try:
    from PIL import Image, ImageChops, ImageEnhance, ImageOps
except ImportError as error:  # pragma: no cover - environment problem, not logic
    raise SystemExit(
        "Pillow is required. Install it with: pip install -r requirements.txt"
    ) from error

UNSPLASH_API = "https://api.unsplash.com"
ACCESS_KEY_ENV = "UNSPLASH_ACCESS_KEY"

DEFAULT_WIDTH = 1600
DEFAULT_HEIGHT = 900
DEFAULT_QUALITY = 90
DEFAULT_TINT = "#808080"

FOCAL_POINTS = {
    "center": (0.5, 0.5),
    "top": (0.5, 0.0),
    "bottom": (0.5, 1.0),
    "left": (0.0, 0.5),
    "right": (1.0, 0.5),
}

# 4x4 ordered dither matrix. Small enough to read as texture at print size.
BAYER_4 = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)


class GeneratorError(RuntimeError):
    """A user-actionable failure in the cover workflow."""


# --------------------------------------------------------------------------
# Credentials
# --------------------------------------------------------------------------


def get_access_key() -> str:
    """Return the Unsplash access key from the environment, or fail loudly.

    The error names the variable but never its value.
    """
    key = (os.environ.get(ACCESS_KEY_ENV) or "").strip()
    if not key:
        raise GeneratorError(
            f"{ACCESS_KEY_ENV} is not set. Register an application at "
            "https://unsplash.com/oauth/applications, copy its Access Key, and "
            "export it in your shell or in a gitignored .env / .envrc that your "
            "shell loads. Do not pass it as a command-line flag and do not paste "
            "it into a chat. Use --input to process a local image without a key."
        )
    return key


def scrub(text: str, secret: str) -> str:
    """Remove the access key from text about to be shown to a human."""
    if not text or not secret:
        return text
    return text.replace(secret, "***")


# --------------------------------------------------------------------------
# Arguments
# --------------------------------------------------------------------------


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a cropped and treated cover image.",
        epilog=(
            "The access key is read from the "
            + ACCESS_KEY_ENV
            + " environment variable only."
        ),
    )
    source = parser.add_argument_group("source")
    source.add_argument(
        "--query",
        help="Unsplash search term. Omit for a random landscape photo.",
    )
    source.add_argument(
        "--input",
        type=Path,
        help="Process an existing local image instead of calling Unsplash.",
    )

    output = parser.add_argument_group("output")
    output.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output image path, extension included. Required, and never guessed.",
    )
    output.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    output.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    output.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    output.add_argument(
        "--focal",
        default="center",
        help="Crop focal point: center, top, bottom, left, right, or x,y from 0 to 1.",
    )
    output.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        help="Lossy output quality from 1 to 100. Default: 90.",
    )

    # Treatments are independent stages, applied in a fixed order:
    # distort, pixelate, hue, duotone, dither.
    treatment = parser.add_argument_group("treatment, applied in this order")
    treatment.add_argument(
        "--distort",
        action="store_true",
        help="Subtle horizontal scanline wave.",
    )
    treatment.add_argument(
        "--pixelate",
        type=int,
        metavar="BLOCK",
        help="Pixel block size in pixels, 2 or more.",
    )
    treatment.add_argument(
        "--hue",
        type=float,
        metavar="DEGREES",
        help="Rotate hue by this many degrees.",
    )
    treatment.add_argument(
        "--duotone",
        action="store_true",
        help="Map the image onto a two-tone ramp built from --tint.",
    )
    treatment.add_argument(
        "--dither",
        action="store_true",
        help="Ordered-dither mesh in --tint over a duotone base. Implies --duotone.",
    )
    treatment.add_argument(
        "--tint",
        default=DEFAULT_TINT,
        help=f"Hex colour for --duotone and --dither. Default: {DEFAULT_TINT}.",
    )
    treatment.add_argument(
        "--cell",
        type=int,
        default=2,
        help="Dither cell size in pixels. Default: 2.",
    )

    parser.add_argument(
        "--app-name",
        default="blog_image_generator",
        help=(
            "Your registered Unsplash application name. Used in the User-Agent "
            "and in the utm_source of attribution links, as Unsplash requires."
        ),
    )

    args = parser.parse_args(argv)

    if args.input and args.query:
        parser.error("Use either --input or --query, not both.")
    if args.width < 1 or args.height < 1:
        parser.error("--width and --height must be positive integers.")
    if args.pixelate is not None and args.pixelate < 2:
        parser.error("--pixelate must be at least 2.")
    if args.cell < 1:
        parser.error("--cell must be at least 1.")
    if not 1 <= args.quality <= 100:
        parser.error("--quality must be between 1 and 100.")
    if args.input and not args.input.is_file():
        parser.error(f"Input image does not exist: {args.input}")
    if args.output.exists() and not args.force:
        parser.error(f"{args.output} already exists. Pass --force to overwrite it.")

    return args


# --------------------------------------------------------------------------
# Unsplash
# --------------------------------------------------------------------------


def request_json(url: str, access_key: str, app_name: str) -> Dict[str, Any]:
    request = Request(
        url,
        headers={
            "Authorization": f"Client-ID {access_key}",
            "Accept-Version": "v1",
            "User-Agent": f"{app_name}/1.0",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        detail = scrub(error.read().decode("utf-8", "replace"), access_key)
        raise GeneratorError(
            f"Unsplash API returned HTTP {error.code}: {detail}"
        ) from error
    except URLError as error:
        raise GeneratorError(f"Could not reach Unsplash: {error.reason}") from error


def fetch_photo(query: Optional[str], access_key: str, app_name: str) -> Dict[str, Any]:
    params = {"orientation": "landscape", "content_filter": "high"}
    if query:
        params["query"] = query
    response = request_json(
        f"{UNSPLASH_API}/photos/random?{urlencode(params)}", access_key, app_name
    )
    if not response.get("id") or not response.get("urls", {}).get("raw"):
        raise GeneratorError("Unsplash did not return a usable photo.")
    return response


def add_image_params(raw_url: str, width: int, height: int) -> str:
    """Add Imgix output parameters while preserving Unsplash's ixid."""
    parts = urlsplit(raw_url)
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    params.update(
        {
            "w": str(width),
            "h": str(height),
            "fit": "crop",
            "crop": "entropy",
            "fm": "jpg",
            "q": "92",
        }
    )
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(params), parts.fragment)
    )


def fetch_image(url: str, app_name: str) -> "Image.Image":
    request = Request(url, headers={"User-Agent": f"{app_name}/1.0"})
    try:
        with urlopen(request, timeout=60) as response:
            image_bytes = response.read()
    except (HTTPError, URLError) as error:
        raise GeneratorError(f"Could not download the selected image: {error}") from error
    with Image.open(io.BytesIO(image_bytes)) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


def track_download(photo: Dict[str, Any], access_key: str, app_name: str) -> str:
    """Ping the download endpoint. Unsplash's API guidelines require this."""
    location = photo.get("links", {}).get("download_location")
    if not location:
        raise GeneratorError("Unsplash did not return a download tracking location.")
    result = request_json(location, access_key, app_name)
    return result.get("url", "recorded")


# --------------------------------------------------------------------------
# Image treatment
# --------------------------------------------------------------------------


def parse_focal(value: str) -> Tuple[float, float]:
    if value in FOCAL_POINTS:
        return FOCAL_POINTS[value]
    try:
        x, y = (float(part.strip()) for part in value.split(",", maxsplit=1))
    except ValueError as error:
        raise GeneratorError(
            "--focal must be center, top, bottom, left, right, or x,y from 0 to 1."
        ) from error
    if not 0 <= x <= 1 or not 0 <= y <= 1:
        raise GeneratorError("Custom --focal coordinates must both be from 0 to 1.")
    return x, y


def parse_colour(value: str) -> Tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(character * 2 for character in text)
    if len(text) != 6:
        raise GeneratorError(f"--tint must be a hex colour such as #3366ff, got {value!r}")
    try:
        return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]
    except ValueError as error:
        raise GeneratorError(
            f"--tint must be a hex colour such as #3366ff, got {value!r}"
        ) from error


def scale_colour(colour: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
    return tuple(max(0, min(255, round(channel * factor))) for channel in colour)  # type: ignore[return-value]


def crop_image(
    image: "Image.Image", width: int, height: int, focal: Tuple[float, float]
) -> "Image.Image":
    return ImageOps.fit(
        image,
        (width, height),
        method=Image.Resampling.LANCZOS,
        centering=focal,
    )


def apply_pixelate(image: "Image.Image", block: int) -> "Image.Image":
    small_size = (
        max(1, round(image.width / block)),
        max(1, round(image.height / block)),
    )
    pixelated = image.resize(small_size, Image.Resampling.BOX).resize(
        image.size, Image.Resampling.NEAREST
    )
    # A small saturation lift keeps the blocks readable without hiding the source.
    return ImageEnhance.Color(pixelated).enhance(1.12)


def apply_hue(image: "Image.Image", degrees: float) -> "Image.Image":
    hue_shift = round((degrees % 360) * 255 / 360)
    hue, saturation, value = image.convert("HSV").split()
    hue = hue.point([(component + hue_shift) % 256 for component in range(256)])
    saturation = ImageEnhance.Contrast(saturation).enhance(1.18)
    treated = Image.merge("HSV", (hue, saturation, value)).convert("RGB")
    return ImageEnhance.Contrast(treated).enhance(1.05)


def duotone_base(image: "Image.Image", tint: Tuple[int, int, int]) -> "Image.Image":
    """Map luminance onto a dark-to-tint ramp."""
    grayscale = ImageOps.grayscale(image)
    grayscale = ImageEnhance.Contrast(grayscale).enhance(1.75)
    grayscale = ImageEnhance.Brightness(grayscale).enhance(0.72)
    return ImageOps.colorize(
        grayscale,
        black=scale_colour(tint, 0.10),
        mid=scale_colour(tint, 0.46),
        white=tint,
    )


def apply_dither(
    image: "Image.Image", cell_size: int, tint: Tuple[int, int, int]
) -> "Image.Image":
    """Composite an ordered-dither mesh in the tint over a duotone base."""
    base = duotone_base(image, tint)
    grayscale = ImageOps.grayscale(image)

    grid_size = (
        max(1, round(image.width / cell_size)),
        max(1, round(image.height / cell_size)),
    )
    sampled = grayscale.resize(grid_size, Image.Resampling.BOX)
    mesh_mask = Image.new("L", grid_size)
    source_pixels = sampled.load()
    mask_pixels = mesh_mask.load()
    for y in range(grid_size[1]):
        for x in range(grid_size[0]):
            threshold = BAYER_4[y % 4][x % 4] * 16 + 8
            mask_pixels[x, y] = 255 if source_pixels[x, y] > threshold else 0

    mask = mesh_mask.resize(image.size, Image.Resampling.NEAREST)
    mask = mask.point(lambda value: round(value * 0.58))
    mesh = Image.new("RGB", image.size, scale_colour(tint, 1.30))
    return Image.composite(mesh, base, mask)


def apply_distortion(image: "Image.Image") -> "Image.Image":
    """Horizontal wave that shifts rows without discarding any source pixel."""
    distorted = Image.new("RGB", image.size)
    for y in range(image.height):
        offset = round(math.sin(y / 13) * 5 + math.sin(y / 43) * 3)
        scanline = image.crop((0, y, image.width, y + 1))
        distorted.paste(ImageChops.offset(scanline, offset, 0), (0, y))
    return distorted


def treat(image: "Image.Image", args: argparse.Namespace) -> "Image.Image":
    tint = parse_colour(args.tint)
    if args.distort:
        image = apply_distortion(image)
    if args.pixelate:
        image = apply_pixelate(image, args.pixelate)
    if args.hue is not None:
        image = apply_hue(image, args.hue)
    if args.dither:
        image = apply_dither(image, args.cell, tint)
    elif args.duotone:
        image = duotone_base(image, tint)
    return image


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def save_image(image: "Image.Image", destination: Path, quality: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = destination.suffix.lower()
    save_args: Dict[str, Any] = {}
    if suffix in {".jpg", ".jpeg", ".webp"}:
        save_args["quality"] = quality
    if suffix == ".webp":
        save_args["method"] = 6
    if suffix in {".jpg", ".jpeg"}:
        save_args["optimize"] = True
    image.save(destination, **save_args)


def metadata_path(destination: Path) -> Path:
    return destination.with_suffix(".source.json")


def local_metadata(source: Path) -> Dict[str, Any]:
    return {
        "provider": "local",
        "source_path": str(source),
        "attribution": None,
        "license": "Unknown. Verify the original licence before publishing.",
    }


def unsplash_metadata(
    photo: Dict[str, Any],
    query: Optional[str],
    source_url: str,
    tracked: str,
    app_name: str,
) -> Dict[str, Any]:
    user = photo.get("user", {})
    user_url = user.get("links", {}).get("html")
    photo_url = photo.get("links", {}).get("html")
    utm = f"utm_source={app_name}&utm_medium=referral"
    user_name = user.get("name") or "Unknown photographer"
    return {
        "provider": "unsplash",
        "license": "Unsplash License, https://unsplash.com/license",
        "selected_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "query": query,
        "photo_id": photo.get("id"),
        "photo_url": f"{photo_url}?{utm}" if photo_url else None,
        "image_url": source_url,
        "photographer": user_name,
        "photographer_url": f"{user_url}?{utm}" if user_url else None,
        "attribution": f"Photo by {user_name} on Unsplash",
        "download_tracking": tracked,
    }


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    focal = parse_focal(args.focal)
    parse_colour(args.tint)  # fail before any network call

    if args.input:
        with Image.open(args.input) as source:
            image = ImageOps.exif_transpose(source).convert("RGB")
        details = local_metadata(args.input)
    else:
        access_key = get_access_key()
        photo = fetch_photo(args.query, access_key, args.app_name)
        source_url = add_image_params(photo["urls"]["raw"], args.width, args.height)
        tracked = track_download(photo, access_key, args.app_name)
        image = fetch_image(source_url, args.app_name)
        details = unsplash_metadata(
            photo, args.query, source_url, tracked, args.app_name
        )

    cover = treat(crop_image(image, args.width, args.height, focal), args)
    save_image(cover, args.output, args.quality)

    details.update(
        {
            "output_path": str(args.output),
            "dimensions": {"width": args.width, "height": args.height},
            "focal": args.focal,
            "treatment": {
                "distort": bool(args.distort),
                "pixelate": args.pixelate,
                "hue": args.hue,
                "duotone": bool(args.duotone or args.dither),
                "dither": bool(args.dither),
                "tint": args.tint if (args.duotone or args.dither) else None,
                "cell": args.cell if args.dither else None,
            },
        }
    )
    sidecar = metadata_path(args.output)
    sidecar.write_text(
        json.dumps(details, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Wrote {args.output} ({args.width}x{args.height})")
    print(f"Wrote source and attribution metadata to {sidecar}")
    if details.get("attribution"):
        print(f"Credit required: {details['attribution']}")


if __name__ == "__main__":
    try:
        main()
    except GeneratorError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
