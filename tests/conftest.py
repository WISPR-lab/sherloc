"""Shared test setup.

The application resolves many paths relative to the `sherloc/` directory
(for example `static_data/app-flags.csv`), so tests run from there.
"""

import os
from pathlib import Path

SHERLOC_DIR = Path(__file__).resolve().parent.parent / "sherloc"
os.chdir(SHERLOC_DIR)

# test_parse_dump.py needs a real phone dump that is gitignored. Skip it
# when the fixture is not present so the rest of the suite can run in CI.
_DUMP_FIXTURE = (
    SHERLOC_DIR
    / "phone_dumps"
    / "83c6500a47585595f72d654829cab29edd2c4f5253e6c05d5576cf04661fd6eb_android.txt"
)

collect_ignore = []
if not _DUMP_FIXTURE.exists():
    collect_ignore.append("test_parse_dump.py")
