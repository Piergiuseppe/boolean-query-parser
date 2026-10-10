"""Copy the package into docs/ so the Pyodide playground runs the current code.

GitHub Pages serves docs/ on its own, so the playground cannot import from the
repository root. Run this after changing the package; tests/test_docs_bundle.py
fails while the copy is stale.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "boolean_query_parser"
BUNDLE = ROOT / "docs" / "boolean_query_parser"
MANIFEST = ROOT / "docs" / "manifest.json"


# The playground only imports the library, never the command line tool.
EXCLUDED = ("cli/", "__main__.py")


def package_files() -> list[str]:
    names = (
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    return sorted(name for name in names if not name.startswith(EXCLUDED))


def manifest() -> str:
    return json.dumps({"package": PACKAGE.name, "files": package_files()}, indent=2) + "\n"


def main() -> None:
    shutil.rmtree(BUNDLE, ignore_errors=True)
    for name in package_files():
        target = BUNDLE / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PACKAGE / name, target)
    MANIFEST.write_text(manifest())
    print(f"copied {len(package_files())} files into {BUNDLE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
