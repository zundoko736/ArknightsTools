import argparse
import csv
from pathlib import Path


def format_csv(file_path):
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    output_path = file_path.with_suffix(".txt")
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter="\t", lineterminator="\n")
        writer.writerows(rows)
    return output_path, rows


def save_combined(rows, output_path=None):
    output_path = Path("combined.txt") if output_path is None else Path(output_path)
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter="\t", lineterminator="\n")
        writer.writerows(rows)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Replace CSV field separators with tabs."
    )
    parser.add_argument("file_paths", nargs="+", type=Path, help="CSV file paths.")
    args = parser.parse_args()

    combined_rows = []
    for file_path in args.file_paths:
        output_path, rows = format_csv(file_path)
        combined_rows.extend(rows)
        print(f"Saved {output_path}")

    print(f"Saved {save_combined(combined_rows)}")


if __name__ == "__main__":
    main()