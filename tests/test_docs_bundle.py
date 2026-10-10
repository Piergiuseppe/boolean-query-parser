import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("sync_docs", ROOT / "scripts" / "sync_docs.py")
sync_docs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_docs)


class DocsBundleTests(unittest.TestCase):
    """The playground in docs/ must run the same code as the package."""

    def test_bundle_matches_the_package(self):
        stale = [
            name
            for name in sync_docs.package_files()
            if not (sync_docs.BUNDLE / name).is_file()
            or (sync_docs.BUNDLE / name).read_bytes() != (sync_docs.PACKAGE / name).read_bytes()
        ]
        self.assertEqual(stale, [], "run: python scripts/sync_docs.py")

    def test_manifest_lists_every_file(self):
        self.assertEqual(
            sync_docs.MANIFEST.read_text(), sync_docs.manifest(), "run: python scripts/sync_docs.py"
        )

    def test_bundle_has_no_leftover_files(self):
        bundled = sorted(
            path.relative_to(sync_docs.BUNDLE).as_posix()
            for path in sync_docs.BUNDLE.rglob("*.py")
            if "__pycache__" not in path.parts
        )
        self.assertEqual(bundled, sync_docs.package_files(), "run: python scripts/sync_docs.py")


if __name__ == "__main__":
    unittest.main()
