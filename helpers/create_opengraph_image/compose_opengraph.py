"""Add clean text and portrait overlays to the rendered batik background."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
IMAGE_DIR = HERE / "images"
INPUT_PATH = IMAGE_DIR / "batik_canvas.png"
OUTPUT_PATH = IMAGE_DIR / "opengraph.png"
ASSETS_DIR = PROJECT_ROOT / "assets"
SITE_ACCESS_PATH = ASSETS_DIR / "opengraph.png"
PORTRAIT_PATH = ASSETS_DIR / "me-800.jpg"

WIDTH, HEIGHT = 1200, 630
NAVY = (0x00, 0x0D, 0x4D)
GREEN = (0x55, 0xCE, 0x58)
WHITE = (255, 255, 255)
PANEL_ALPHA = round(0.85 * 255)

TEXT_OUTER_BOX = (34, 45, 691, 585)
TEXT_INNER_BOX = (39, 50, 686, 580)
PORTRAIT_OUTER_BOX = (792, 66, 1163, 566)
PORTRAIT_INNER_BOX = (800, 74, 1155, 558)

HEADLINE = "Hi, I'm Aaron!"
BODY = "I'm a PhD Student\nat Stanford GSB."
FOOTER = "This is my website."

FONT_DIR = PROJECT_ROOT / "fonts" / "Atkinson Hyperlegible Next" / "otf"
HEADLINE_FONT = FONT_DIR / "AtkinsonHyperlegibleNext-Bold.otf"
BODY_FONT = FONT_DIR / "AtkinsonHyperlegibleNext-Regular.otf"
HEADLINE_SIZE = 66
BODY_SIZE = 50


def portrait_layer() -> tuple[Image.Image, Image.Image]:
    x0, y0, x1, y1 = PORTRAIT_INNER_BOX
    size = (x1 - x0 + 1, y1 - y0 + 1)

    with Image.open(PORTRAIT_PATH) as source:
        portrait = ImageOps.fit(
            source.convert("RGB"),
            size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.33),
        )

    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1),
        radius=27,
        fill=255,
    )
    return portrait, mask


def render() -> Image.Image:
    with Image.open(INPUT_PATH) as source:
        if source.size != (WIDTH, HEIGHT):
            raise ValueError(f"{INPUT_PATH.name} must be {WIDTH} x {HEIGHT}")
        canvas = source.convert("RGBA")

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Opaque green rings with a 95%-opaque navy text-panel interior.
    overlay_draw.rounded_rectangle(TEXT_OUTER_BOX, radius=34, fill=(*GREEN, 255))
    overlay_draw.rounded_rectangle(
        TEXT_INNER_BOX,
        radius=30,
        fill=(*NAVY, PANEL_ALPHA),
    )
    overlay_draw.rounded_rectangle(
        PORTRAIT_OUTER_BOX,
        radius=34,
        fill=(*GREEN, 255),
    )
    canvas = Image.alpha_composite(canvas, overlay)

    draw = ImageDraw.Draw(canvas)
    headline_font = ImageFont.truetype(HEADLINE_FONT, HEADLINE_SIZE)
    body_font = ImageFont.truetype(BODY_FONT, BODY_SIZE)

    # Preserve the original baselines despite the Next faces' taller metrics.
    draw.text((64, 124), HEADLINE, font=headline_font, fill=WHITE)
    draw.multiline_text(
        (64, 272),
        BODY,
        font=body_font,
        fill=WHITE,
        spacing=5,
    )
    draw.text((63, 465), FOOTER, font=body_font, fill=WHITE)

    portrait, portrait_mask = portrait_layer()
    canvas.paste(portrait, PORTRAIT_INNER_BOX[:2], portrait_mask)
    return canvas.convert("RGB")


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    render().save(OUTPUT_PATH, format="PNG")
    render().save(SITE_ACCESS_PATH, format="PNG")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
