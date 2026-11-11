import argparse
import csv
import json
from pathlib import Path


INVALID_FILENAME_CHARACTERS = set('<>:"/\\|?*')


def extract_data(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        data = json.load(file)

    extracted_data = [
        (
            "#",
            "　".join(
                (
                    data.get("eventName") or "",
                    data.get("storyCode") or "",
                    data.get("avgTag") or "",
                    data.get("storyName") or "",
                )
            ),
        ),
    ]
    for entry in data.get("storyList", []):
        attributes = entry.get("attributes", {})
        if entry.get("prop") == "name":
            content = attributes.get("content", "")
            if content.startswith("  "):
                content = content[2:]
            extracted_data.append((attributes.get("name", ""), content))
        elif entry.get("prop") == "Sticker" and "text" in attributes:
            extracted_data.append(("@", attributes["text"]))
        elif entry.get("prop") == "Delay":
            extracted_data.append(("", "", ""))

    return extracted_data


def _output_path(file_path, output_path, header):
    output_dir = Path(file_path).parent if output_path is None else Path(output_path).parent
    filename = "".join(
        "_" if character in INVALID_FILENAME_CHARACTERS or ord(character) < 32 else character
        for character in header
    ).rstrip(" .")
    if not filename:
        raise ValueError(f"Story header cannot be used as a filename: {file_path}")
    return output_dir / f"{filename}.csv"


def get_output_path(file_path, output_path=None):
    extracted_data = extract_data(file_path)
    return _output_path(file_path, output_path, extracted_data[0][1])


def make_output_paths_unique(output_paths):
    reserved_paths = set(output_paths)
    used_paths = set()
    unique_paths = []
    for output_path in output_paths:
        if output_path in used_paths:
            suffix = 2
            while True:
                candidate = output_path.with_name(
                    f"{output_path.stem} ({suffix}){output_path.suffix}"
                )
                if candidate not in reserved_paths and candidate not in used_paths:
                    output_path = candidate
                    break
                suffix += 1
        used_paths.add(output_path)
        unique_paths.append(output_path)
    return unique_paths


def save_csv(file_path, output_path=None, on_saved=None):
    extracted_data = extract_data(file_path)
    output_path = (
        _output_path(file_path, None, extracted_data[0][1])
        if output_path is None
        else Path(output_path)
    )
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerows(extracted_data)
    if on_saved is None:
        print(f"Saved {output_path}")
    else:
        on_saved(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Extract story text into CSV files.")
    parser.add_argument("file_paths", nargs="+", type=Path, help="Input JSON file paths.")
    args = parser.parse_args()

    output_paths = make_output_paths_unique(
        [get_output_path(file_path) for file_path in args.file_paths]
    )

    for file_path, output_path in zip(args.file_paths, output_paths):
        save_csv(file_path, output_path)

if __name__ == "__main__":
    main()
