"""Every file this demonstration reads, and where it came from.

All three are NHS England primary outputs for August 2026 (published
8 October 2026), at the same URLs my August 2026 verification pipeline uses.
NHS England rotates the random suffixes on its file URLs when it revises a
month. If one of these 404s, find the month on `source_page` and update it
here; the SHA-256 in each metadata.json tells you whether you got my bytes.
"""

from __future__ import annotations

NHSE = "https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2"
RTT_2026_27 = "https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/rtt-data-2026-27/"

SOURCES: list[dict] = [
    {
        "slug": "nhse_rtt_2026-08",
        "publisher": "NHS England",
        "publication_name": "Consultant-led RTT Waiting Times - full CSV extract, August 2026",
        "source_page": RTT_2026_27,
        "vintage": "as first published, 8 Oct 2026",
        "files": [(
            "Full-CSV-data-file-Aug26-ZIP-3M-vjgRdG.zip",
            f"{NHSE}/2026/10/Full-CSV-data-file-Aug26-ZIP-3M-vjgRdG.zip",
            "Provider x commissioner x RTT part x treatment function x weekly wait bands (0-104+). "
            "The only input to the star schema.",
        )],
    },
    {
        "slug": "nhse_rtt_published_2026-08",
        "publisher": "NHS England",
        "publication_name": "RTT Waiting Times, August 2026 - statistical press notice and Incomplete Provider workbook",
        "source_page": RTT_2026_27,
        "vintage": "as first published, 8 Oct 2026",
        "files": [
            ("Aug26-RTT-statistical-press-notice-PDF-389K-vjgRdG.pdf",
             f"{NHSE}/2026/10/Aug26-RTT-statistical-press-notice-PDF-389K-vjgRdG.pdf",
             "Table 1: incomplete pathways and % within 18 weeks by treatment function, England, "
             "not including estimates for missing trusts. Gate T target."),
            ("Incomplete-Provider-Aug26-XLSX-9M-vjgRdG.xlsx",
             f"{NHSE}/2026/10/Incomplete-Provider-Aug26-XLSX-9M-vjgRdG.xlsx",
             "Published provider x treatment function incomplete pathways. Gate P target."),
        ],
    },
]
