import json
from pathlib import Path


PROJECT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


def load_json(name):
    path = PROJECT / "config" / name

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )






