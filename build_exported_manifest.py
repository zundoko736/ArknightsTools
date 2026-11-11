import gzip
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPORTED_DIR = ROOT / "exported"
MANIFEST_PATH = ROOT / "exported-manifest.json"
CORPUS_PATH = ROOT / "exported-corpus.json.gz"


def main():
    if not EXPORTED_DIR.is_dir():
        raise FileNotFoundError(f"Search directory does not exist: {EXPORTED_DIR}")

    paths = sorted(
        path
        for path in EXPORTED_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() == ".txt"
    )
    files = [path.relative_to(ROOT).as_posix() for path in paths]
    MANIFEST_PATH.write_text(
        json.dumps({"files": files}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with CORPUS_PATH.open("wb") as output_file:
        with gzip.GzipFile(
            filename="",
            fileobj=output_file,
            mode="wb",
            compresslevel=9,
            mtime=0,
        ) as compressed_file:
            with io.TextIOWrapper(compressed_file, encoding="utf-8") as corpus:
                corpus.write('{"files":[')
                for index, path in enumerate(paths):
                    if index:
                        corpus.write(",")
                    json.dump(
                        {
                            "path": path.relative_to(ROOT).as_posix(),
                            "content": path.read_text(encoding="utf-8-sig"),
                        },
                        corpus,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    )
                corpus.write("]}")

    print(f"Wrote {len(files)} text-file paths to {MANIFEST_PATH}")
    print(f"Wrote compressed story text to {CORPUS_PATH}")


if __name__ == "__main__":
    main()
