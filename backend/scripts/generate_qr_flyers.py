"""Generate a high-resolution QR PNG for the exhibition flyer.

Single QR encodes the signup deep-link with the invite code pre-filled:
``https://aidwiseai.com/signup?invite=AIRU2026``. Error-correction level
``H`` (~30%) so a partly damaged or sticker-covered print still scans.

The output is written to ``backend/out/exhibition/aidwise-airu2026-qr.png``;
the directory is created on demand. Print at 5cm × 5cm minimum so phone
cameras at 30-50 cm scan reliably.
"""
from __future__ import annotations

from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H


CODE = "AIRU2026"
DEEP_LINK = f"https://aidwiseai.com/signup?invite={CODE}"
OUT_DIR = Path(__file__).resolve().parents[1] / "out" / "exhibition"
OUT_PATH = OUT_DIR / f"aidwise-{CODE.lower()}-qr.png"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,
        box_size=20,
        border=4,
    )
    qr.add_data(DEEP_LINK)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(OUT_PATH)

    print(f"QR saved: {OUT_PATH} ({img.size[0]}x{img.size[1]} px)")
    print(f"Deep link: {DEEP_LINK}")
    print(
        "\nFlyer copy suggestion:\n"
        "AidwiseAI - Free 30-day Pro trial for Air University students\n"
        "Scan to claim personalised scholarship matching, SOP drafting,\n"
        "and visa interview practice.\n"
        f"Code: {CODE}  |  aidwiseai.com  |  Valid May 19-26 only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
