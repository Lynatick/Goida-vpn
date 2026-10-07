import base64
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from combined_subscription import build_combined_subscriptions
from subscription_converter import ConversionError


class CombinedSubscriptionTest(unittest.TestCase):
    def test_mixed_encodings_duplicates_and_repeated_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mirror = root / "githubmirror"
            mirror.mkdir()
            first = "trojan://secret@one.example:443#First"
            second = "trojan://secret@two.example:443#Second"
            mirror.joinpath("1.txt").write_text(first + "\n" + first)
            mirror.joinpath("2.txt").write_text(base64.b64encode(
                ("# Comment\n" + first + "\n" + second).encode()
            ).decode())
            mirror.joinpath("all.txt").write_text("trojan://old@old.example:443")
            with redirect_stdout(io.StringIO()):
                paths = build_combined_subscriptions(root)
            self.assertEqual(paths, ["githubmirror/all.txt", "raw/all.txt", "hiddify/all.json"])
            self.assertEqual(mirror.joinpath("all.txt").read_text(), first + "\n" + second + "\n")
            raw = json.loads(root.joinpath("raw/all.txt").read_text())
            self.assertEqual([item["server"] for item in raw["outbounds"]], ["one.example", "two.example"])
            profile = json.loads(root.joinpath("hiddify/all.json").read_text())
            self.assertEqual(profile["route"]["final"], "select")
            self.assertEqual(profile["outbounds"][1]["outbounds"], [item["tag"] for item in raw["outbounds"]])
            before = {path: root.joinpath(path).read_text() for path in paths}
            with redirect_stdout(io.StringIO()):
                build_combined_subscriptions(root)
            self.assertEqual(before, {path: root.joinpath(path).read_text() for path in paths})

    def test_native_json_cannot_overwrite_existing_aggregate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mirror = root / "githubmirror"
            mirror.mkdir()
            mirror.joinpath("1.txt").write_text(json.dumps({
                "outbounds": [{"type": "trojan", "tag": "proxy"}],
                "route": {"rules": [{"outbound": "proxy"}]}
            }))
            mirror.joinpath("all.txt").write_text("previous")
            with self.assertRaises(ConversionError):
                build_combined_subscriptions(root)
            self.assertEqual(mirror.joinpath("all.txt").read_text(), "previous")
            self.assertFalse(root.joinpath("raw/all.txt").exists())


if __name__ == "__main__":
    unittest.main()
