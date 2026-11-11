import argparse
from pathlib import Path
import sys


def iter_matches(parent_dir, text=None, by_text=None):
    parent_dir = parent_dir.resolve()
    if not parent_dir.is_dir():
        raise NotADirectoryError(f"Search directory does not exist: {parent_dir}")

    text_files = sorted(
        path for path in parent_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".txt"
    )
    for text_file in text_files:
        with text_file.open("r", encoding="utf-8-sig") as file:
            for line_number, line in enumerate(file, start=1):
                before_tab, separator, after_tab = line.partition("\t")
                searchable_text = after_tab if separator else line
                if (
                    (text is None or text in searchable_text)
                    and (
                        by_text is None
                        or (
                            separator
                            and by_text in before_tab
                        )
                    )
                ):
                    yield f"{text_file.name[:-4]}\t{line_number}\t{line.rstrip()}"


def search_text(parent_dir, text=None, by_text=None):
    for match in iter_matches(parent_dir, text, by_text):
        print(match)


def main():
    parser = argparse.ArgumentParser(
        description="Search recursively through text files."
    )
    parser.add_argument(
        "parent_dir",
        type=Path,
        help="Parent directory to search recursively.",
    )
    parser.add_argument("text", nargs="?", help="Text to search for after the tab.")
    parser.add_argument(
        "--by",
        help="Search for this text before the first tab character.",
    )
    args = parser.parse_args()
    if args.text is None and args.by is None:
        parser.error("provide text, --by, or both")
    sys.stdout.reconfigure(errors="backslashreplace")
    search_text(args.parent_dir, args.text, args.by)


if __name__ == "__main__":
    main()