import argparse
from pathlib import Path

import extractor
import formatter


def export_directory(input_dir, output_dir=None, progress_callback=None):
    input_dir = input_dir.resolve()
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {input_dir}")

    if output_dir is None:
        output_dir = Path(__file__).resolve().parent / "exported"
    else:
        output_dir = Path(output_dir).resolve()
    json_files = sorted(
        path for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".json"
    )
    output_files = [
        (
            json_path,
            extractor.get_output_path(
                json_path,
                (output_dir / json_path.relative_to(input_dir)).with_suffix(".csv"),
            ),
        )
        for json_path in json_files
    ]
    csv_paths = extractor.make_output_paths_unique(
        [csv_path for _, csv_path in output_files]
    )
    output_files = [
        (json_path, csv_path)
        for (json_path, _), csv_path in zip(output_files, csv_paths)
    ]

    for json_path, csv_path in output_files:
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            extractor.save_csv(json_path, csv_path, on_saved=lambda _: None)
            output_path, _ = formatter.format_csv(csv_path)
            if progress_callback is None:
                print(f"Saved {output_path}")
            else:
                progress_callback(output_path)
        finally:
            csv_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Extract JSON stories and export formatted text files."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory to search recursively for JSON files.",
    )
    args = parser.parse_args()
    export_directory(args.input_dir)


if __name__ == "__main__":
    main()