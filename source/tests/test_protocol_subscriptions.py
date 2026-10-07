from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from protocol_subscriptions import build_protocol_subscriptions
from subscription_converter import ConversionError
from subscription_report import render_subscription_rows


class ProtocolSubscriptionTest(unittest.TestCase):
    def test_single_protocol_groups_preserve_tls_and_exclude_invalid_node(self):
        vless = {
            "type": "vless", "tag": "VLESS", "server": "vless.example", "server_port": 443,
            "uuid": "cbb3f877-d1fb-344c-87a9-d153bffd5484",
            "tls": {"enabled": True, "reality": {"enabled": True, "public_key": "test-key"}}
        }
        trojan = {"type": "trojan", "tag": "Trojan", "server": "trojan.example", "server_port": 443, "password": "secret"}
        config = {"outbounds": [vless, trojan, dict(vless, uuid="invalid"), dict(trojan, server_port=0)], "endpoints": []}
        original = deepcopy(config)
        with tempfile.TemporaryDirectory() as directory, redirect_stdout(io.StringIO()):
            paths, counts = build_protocol_subscriptions(config, directory)
            self.assertEqual(config, original)
            self.assertEqual(counts, {"trojan": 1, "vless": 1})
            for kind in counts:
                raw = json.loads(Path(directory, f"raw/by-type/{kind}.json").read_text())
                self.assertEqual({node["type"] for node in raw["outbounds"]}, {kind})
                profile = json.loads(Path(directory, f"hiddify/by-type/{kind}.json").read_text())
                self.assertEqual(profile["outbounds"][3:], raw["outbounds"])
                self.assertEqual(profile["outbounds"][2]["outbounds"], [raw["outbounds"][0]["tag"]])
            self.assertEqual(json.loads(Path(directory, "protocol-stats.json").read_text())["excluded"], 2)
            self.assertIn("hiddify/by-type/vless.json", paths)

    def test_invalid_dataset_or_native_rules_do_not_overwrite_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path(directory, "protocol-stats.json")
            previous.write_text("previous")
            for config in (
                {"outbounds": [{"type": "trojan", "server": "example.com", "server_port": 443}]},
                {"outbounds": [{"type": "trojan"}], "route": {"rules": [{"outbound": "proxy"}]}}
            ):
                with self.assertRaises(ConversionError):
                    build_protocol_subscriptions(config, directory)
                self.assertEqual(previous.read_text(), "previous")

    def test_table_links_only_in_combined_row_and_use_copy_buttons(self):
        rows = {"all": {"configs": 2, "excluded": 0}, "1": {"configs": 2, "excluded": 0}}
        html = render_subscription_rows(rows, {"vless": 2})
        self.assertIn('rowspan="2"', html)
        self.assertEqual(html.count('data-copy="protocol-vless"'), 1)
        self.assertIn('/hiddify/by-type/vless.json', html)
        self.assertIn('>vless.json</a>', html)


if __name__ == "__main__":
    unittest.main()
