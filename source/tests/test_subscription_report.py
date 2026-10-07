import base64
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from combined_subscription import build_combined_subscriptions
from subscription_report import subscription_counts


class SubscriptionReportTest(unittest.TestCase):
    def test_conversion_exclusions_and_base64(self):
        content = "# comment\ntrojan://secret@one.example:443\nunsupported://node\nbroken line\n"
        expected = {"configs": 1, "excluded": 2}
        self.assertEqual(subscription_counts(content), expected)
        self.assertEqual(subscription_counts(base64.b64encode(content.encode()).decode()), expected)

    def test_all_invalid_entries_and_empty_source(self):
        self.assertEqual(subscription_counts("unsupported://one\nbroken line"), {"configs": 0, "excluded": 2})
        self.assertEqual(subscription_counts(""), {"configs": 0, "excluded": 0})
        self.assertEqual(subscription_counts('{"outbounds": "invalid"}'), {"configs": None, "excluded": None})

    def test_native_config_counts_servers_without_selection_groups(self):
        content = json.dumps({
            "outbounds": [{"type": "direct"}, {"type": "selector"}, {"type": "trojan"}],
            "endpoints": [{"type": "wireguard"}]
        })
        self.assertEqual(subscription_counts(content), {"configs": 2, "excluded": 0})

    def test_combined_report_deduplicates_and_updates_homepage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mirror = root / "githubmirror"
            mirror.mkdir()
            node = "trojan://secret@one.example:443"
            mirror.joinpath("1.txt").write_text(node + "\nunsupported://one\nbroken line")
            mirror.joinpath("2.txt").write_text(node + "\nunsupported://one")
            homepage = root / "index.html"
            homepage.write_text("before<!-- subscription-report:start -->old<!-- subscription-report:end -->after")
            with redirect_stdout(io.StringIO()):
                paths = build_combined_subscriptions(root)
            report = json.loads(root.joinpath("subscription-stats.json").read_text())
            self.assertEqual(report["all"], {"configs": 1, "excluded": 2})
            self.assertEqual(report["1"], {"configs": 1, "excluded": 2})
            self.assertEqual(report["2"], {"configs": 1, "excluded": 1})
            self.assertIn("index.html", paths)
            html = homepage.read_text()
            self.assertTrue(html.startswith("before"))
            self.assertTrue(html.endswith("after"))
            self.assertIn('<th scope="row">Все</th><td>1</td><td>2</td>', html)
            self.assertNotIn("secret", root.joinpath("subscription-stats.json").read_text())


if __name__ == "__main__":
    unittest.main()
