from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from subscription_verifier import SubscriptionVerifier
from subscription_converter import ConversionError


class SubscriptionVerifierTest(unittest.TestCase):
    def verifier(self, directory):
        with patch("subscription_verifier.importlib.util.find_spec", return_value=True):
            return SubscriptionVerifier(core=__file__, report_dir=directory)

    def test_sequential_filter_only_accepts_video_received(self):
        with tempfile.TemporaryDirectory() as directory:
            verifier = self.verifier(directory)
            content = "\n".join(f"trojan://secret@node{i}.example:443#{i}" for i in range(3))
            sequence = []
            def check(node, *args):
                sequence.append(node["server"])
                return {"status": ["connection_failed", "media_received", "inconclusive"][len(sequence) - 1]}
            with patch("subscription_verifier.check_node", side_effect=check), redirect_stdout(io.StringIO()):
                filtered = verifier.filter_subscription(content, "githubmirror/4.txt")
            self.assertEqual(sequence, ["node0.example", "node1.example", "node2.example"])
            self.assertEqual(filtered, content.splitlines()[1] + "\n")
            self.assertEqual(len(Path(directory, "4.jsonl").read_text().splitlines()), 3)

    def test_no_passed_servers_rejects_whole_source(self):
        with tempfile.TemporaryDirectory() as directory:
            verifier = self.verifier(directory)
            with patch("subscription_verifier.check_node", return_value={"status": "inconclusive"}), redirect_stdout(io.StringIO()):
                with self.assertRaises(ConversionError):
                    verifier.filter_subscription("trojan://secret@host.example:443", "1.txt")

    def test_native_rules_not_trimmed_when_one_server_fails(self):
        config = {
            "outbounds": [{"type": "trojan", "tag": tag, "server": tag + ".example"} for tag in ("one", "two")],
            "route": {"rules": [{"domain": ["example.com"], "outbound": "two"}]}
        }
        with tempfile.TemporaryDirectory() as directory:
            verifier = self.verifier(directory)
            with patch("subscription_verifier.check_node", side_effect=[{"status": "media_received"}, {"status": "connection_failed"}]), redirect_stdout(io.StringIO()):
                with self.assertRaises(ConversionError):
                    verifier.filter_subscription(json.dumps(config), "1.txt")
            with patch("subscription_verifier.check_node", return_value={"status": "media_received"}), redirect_stdout(io.StringIO()):
                self.assertEqual(json.loads(verifier.filter_subscription(json.dumps(config), "1.txt")), config)


if __name__ == "__main__":
    unittest.main()
