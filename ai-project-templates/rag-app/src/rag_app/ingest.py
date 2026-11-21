"""Load raw docs, split into chunks, save to data/processed/chunks.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed" / "chunks.json"


def chunk(text: str, source: str) -> list[dict]:
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
    return [{"id": f"{source}#{i}", "source": source, "text": l} for i, l in enumerate(lines)]


def main() -> None:
    chunks = [c for f in sorted(RAW.glob("*.[mt][dx]*")) for c in chunk(f.read_text(), f.name)]
    OUT.write_text(json.dumps(chunks, indent=2))
    print(f"Wrote {len(chunks)} chunks to {OUT}")


if __name__ == "__main__":
    main()
