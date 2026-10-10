import io
import json
import os
import tempfile
import unittest

from boolean_query_parser.cli import main

LOG = (
    "2025-03-15 ERROR request took 1500ms size 12MB\n"
    "2025-03-15 INFO healthcheck ok 20ms\n"
    "2025-03-16 ERROR timeout after 30s\n"
)


class CliTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.log = os.path.join(directory.name, "app.log")
        with open(self.log, "w", encoding="utf-8") as handle:
            handle.write(LOG)
        self.jsonl = os.path.join(directory.name, "app.jsonl")
        with open(self.jsonl, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"level": "error", "ms": 900}) + "\n")
            handle.write("not json\n")
            handle.write(json.dumps({"level": "info", "ms": 12}) + "\n")

    def run_cli(self, *argv, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        status = main(list(argv), stdin=io.StringIO(stdin), stdout=out, stderr=err)
        return status, out.getvalue(), err.getvalue()

    def test_prints_matching_lines(self):
        status, out, _ = self.run_cli("ERROR dur:>1s", self.log)
        self.assertEqual(status, 0)
        self.assertEqual(out.splitlines(), [LOG.splitlines()[0], LOG.splitlines()[2]])

    def test_reads_stdin(self):
        status, out, _ = self.run_cli("pyth*", stdin="python rocks\nruby\n")
        self.assertEqual((status, out), (0, "python rocks\n"))

    def test_options(self):
        self.assertEqual(self.run_cli("-i", "-n", "info", self.log)[1], "2:" + LOG.splitlines()[1] + "\n")
        self.assertEqual(self.run_cli("-v", "ERROR", self.log)[1], LOG.splitlines()[1] + "\n")
        self.assertEqual(self.run_cli("-c", "ERROR", self.log)[1], "2\n")
        self.assertEqual(self.run_cli("-c", "ERROR", self.log, self.log)[1], f"{self.log}:2\n{self.log}:2\n")
        self.assertEqual(self.run_cli("-l", "ERROR", self.log)[1], f"{self.log}\n")
        self.assertEqual(self.run_cli("-w", "ERRO", self.log)[0], 1)

    def test_color_highlights_hits(self):
        _, out, _ = self.run_cli("--color", "always", "timeout", self.log)
        self.assertIn("\033[1;31mtimeout\033[0m", out)

    def test_explain(self):
        _, out, _ = self.run_cli("--explain", "timeout", self.log)
        self.assertEqual(out, LOG.splitlines()[2] + "\n    ✓ Text('timeout')  at 17-24\n")

    def test_json_records_skip_bad_lines_and_report_them(self):
        status, out, err = self.run_cli("--json", "level:error ms:num:>500", self.jsonl)
        self.assertEqual(status, 2)
        self.assertEqual(out, '{"level": "error", "ms": 900}\n')
        self.assertIn("line 2 is not valid JSON", err)

    def test_exit_statuses(self):
        self.assertEqual(self.run_cli("zzz", self.log)[0], 1)
        status, _, err = self.run_cli("a AND", self.log)
        self.assertEqual(status, 2)
        self.assertIn("Unexpected end of query", err)
        self.assertEqual(self.run_cli("--no-regex", "/x/", self.log)[0], 2)
        status, _, err = self.run_cli("x", self.log + ".missing")
        self.assertEqual(status, 2)
        self.assertIn("No such file", err)

    def test_field_query_on_plain_text_points_to_json(self):
        status, _, err = self.run_cli("level:error", self.log)
        self.assertEqual(status, 2)
        self.assertIn("--json", err)


if __name__ == "__main__":
    unittest.main()
