"""Shared helpers for the fan-out join demonstration.

The RTT measure rules here are the ones from my August 2026 verification
pipeline (nhs-rtt-august-2026-verification), which in turn copied them from
Two Maps. I don't invent a new measure for this piece: the point is that the
correct-grain figures are the same figures NHS England publishes, so the
fan-out is a distortion of a verified baseline, not a second guess.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
BRONZE_DIR = REPO_ROOT / "data" / "bronze"
SILVER_DIR = REPO_ROOT / "data" / "silver"
GOLD_DIR = REPO_ROOT / "data" / "gold"
STAR_DIR = SILVER_DIR / "star"

USER_AGENT = "rtt-fan-out-join/0.1"

PERIOD = "2026-08"

#: Commissioner code for activity with no identified commissioner. NHS
#: England's published Incomplete Provider workbook and press notice Table 1
#: both exclude these rows, so I drop them too (same rule as the verification
#: pipeline and Two Maps).
RTT_UNIDENTIFIED_COMMISSIONER = "NONC"

#: The extract's all-specialty row. It is a subtotal, not a treatment
#: function, so it never goes into the fact table. I keep it only to check
#: that the named treatment functions add back up to it.
TOTAL_TF_CODE = "C_999"

#: The 18-week standard. A pathway in band "Gt 17 To 18 Weeks" is within 18
#: weeks; one in "Gt 18 To 19 Weeks" is over.
STANDARD_WEEKS = 18

#: (old code, surviving code, first period the survivor carries the old trust).
#: Copied from the verification pipeline: the only merger in April 2025 -
#: August 2026 is North Bristol (RVJ) into Bristol NHS FT (RA7), 1 July 2026.
TRUST_SUCCESSIONS = [
    ("RVJ", "RA7", "2026-07"),
]


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path, timeout: int = 600) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=timeout, headers={"User-Agent": USER_AGENT}) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    # I only rename once the whole payload has landed, so a dropped connection
    # can never leave a truncated file in Bronze looking complete.
    tmp.rename(dest)
    return dest


def write_metadata(folder: Path, **fields) -> None:
    fields["written_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (folder / "metadata.json").write_text(json.dumps(fields, indent=2) + "\n")


def band_lower_week(col: str) -> int:
    """'Gt 17 To 18 Weeks SUM 1' -> 17; 'Gt 104 Weeks SUM 1' -> 104."""
    return int(col.split()[1])
