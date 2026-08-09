"""Download the redwood image and create its foreground mask with rembg."""

from pathlib import Path
from urllib.request import Request, urlopen

from rembg import new_session, remove


HERE = Path(__file__).resolve().parent
IMAGE_DIR = HERE / "images"
SOURCE_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/2/2c/MetaseqLeaves.jpg"
)
ORIGINAL_PATH = IMAGE_DIR / "redwood_leaf_original.jpg"
MASK_PATH = IMAGE_DIR / "redwood_leaf_mask.png"
MODEL_NAME = "bria-rmbg"


def create_mask() -> tuple[Path, Path]:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    request = Request(SOURCE_URL, headers={"User-Agent": "create-rembg-mask"})
    with urlopen(request) as response:
        original = response.read()

    # Preserve the exact downloaded bytes separately from the generated mask.
    ORIGINAL_PATH.write_bytes(original)

    # This downloads and verifies the model on first use, then loads its cache.
    session = new_session(MODEL_NAME)
    mask = remove(
        original,
        session=session,
        only_mask=True,
        force_return_bytes=True,
    )
    MASK_PATH.write_bytes(mask)
    return ORIGINAL_PATH, MASK_PATH


def main() -> None:
    original_path, mask_path = create_mask()
    print(original_path)
    print(mask_path)


if __name__ == "__main__":
    main()
