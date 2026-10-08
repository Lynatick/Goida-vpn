from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest

from hiddify_subscription import YOUTUBE_TEST_URL, build_hiddify_config, save_hiddify_subscription
from subscription_converter import ConversionError


def sample_config():
    return {
        "outbounds": [{
            "type": "vless", "tag": "🇭🇰 Proxy", "server": "host.test",
            "server_port": 443, "uuid": "cbb3f877-d1fb-344c-87a9-d153bffd5484",
            "tls": {"enabled": True, "reality": {
                "enabled": True, "public_key": "key", "short_id": "abcd"
            }}
        }],
        "endpoints": []
    }


class HiddifySubscriptionTest(unittest.TestCase):
    def test_generated_selector_and_urltest_reference_existing_nodes(self):
        config = sample_config()
        profile = build_hiddify_config(config)
        selector, automatic, node = profile["outbounds"]
        self.assertEqual(selector["type"], "selector")
        self.assertEqual(automatic["type"], "urltest")
        self.assertEqual(selector["default"], automatic["tag"])
        self.assertEqual(selector["outbounds"], [automatic["tag"], node["tag"]])
        self.assertEqual(automatic["outbounds"], [node["tag"]])
        self.assertEqual(selector["tag"], "Выбор сервера")
        self.assertEqual(automatic["tag"], "Автовыбор · YouTube")
        self.assertEqual(automatic["url"], YOUTUBE_TEST_URL)
        self.assertEqual(sum(item["type"] == "urltest" for item in profile["outbounds"]), 1)
        self.assertEqual(profile["route"]["final"], selector["tag"])
        self.assertEqual(automatic["interval"], "3m")
        self.assertEqual(node, config["outbounds"][0])

    def test_preserves_rules_dns_reality_and_input_with_tag_collisions(self):
        config = sample_config()
        config["outbounds"][0]["tag"] = "Автовыбор · YouTube"
        config["outbounds"].extend([
            {"type": "direct", "tag": "direct"},
            {"type": "selector", "tag": "Выбор сервера", "outbounds": ["Автовыбор · YouTube"]}
        ])
        config["route"] = {"rules": [{"ip_is_private": True, "outbound": "direct"}], "final": "Автовыбор · YouTube"}
        config["dns"] = {"servers": [{"type": "udp", "server": "1.1.1.1"}]}
        original = deepcopy(config)
        profile = build_hiddify_config(config)
        self.assertEqual(config, original)
        self.assertEqual(profile["route"]["rules"], config["route"]["rules"])
        self.assertEqual(profile["dns"], config["dns"])
        self.assertEqual(profile["outbounds"][2:], config["outbounds"])
        self.assertEqual(profile["outbounds"][0]["tag"], "Выбор сервера-1")
        self.assertEqual(profile["outbounds"][1]["tag"], "Автовыбор · YouTube-1")
        self.assertEqual(profile["outbounds"][1]["outbounds"], ["Автовыбор · YouTube"])

    def test_youtube_tag_collision_keeps_existing_route_reference(self):
        config = sample_config()
        config["outbounds"][0]["tag"] = "Автовыбор · YouTube"
        config["route"] = {"rules": [{"domain": ["example.com"], "outbound": "Автовыбор · YouTube"}]}
        profile = build_hiddify_config(config)
        youtube = profile["outbounds"][1]
        self.assertEqual(youtube["tag"], "Автовыбор · YouTube-1")
        self.assertEqual(youtube["outbounds"], ["Автовыбор · YouTube"])
        self.assertEqual(profile["route"]["rules"], config["route"]["rules"])
        self.assertIn(youtube["tag"], profile["outbounds"][0]["outbounds"])

    def test_wireguard_endpoint_and_missing_tags_are_selectable(self):
        config = {"endpoints": [{"type": "wireguard", "private_key": "key"}]}
        profile = build_hiddify_config(config)
        tag = profile["endpoints"][0]["tag"]
        self.assertEqual(profile["outbounds"][1]["outbounds"], [tag])
        self.assertNotIn("tag", config["endpoints"][0])

    def test_duplicate_tags_rejected(self):
        config = sample_config()
        config["outbounds"].append(deepcopy(config["outbounds"][0]))
        with self.assertRaises(ConversionError):
            build_hiddify_config(config)

    def test_direct_only_and_xray_configs_are_not_mislabelled_as_hiddify(self):
        for config in (
            {"outbounds": [{"type": "direct", "tag": "direct"}]},
            {"outbounds": [{"protocol": "vless", "tag": "proxy", "settings": {}}]}
        ):
            with self.subTest(config=config), self.assertRaises(ConversionError):
                build_hiddify_config(config)

    def test_array_profiles_saved_separately_with_independent_rules(self):
        configs = [sample_config(), sample_config()]
        configs[0]["route"] = {"rules": [{"domain": ["first.test"], "outbound": "🇭🇰 Proxy"}]}
        configs[1]["route"] = {"rules": [{"domain": ["second.test"], "outbound": "🇭🇰 Proxy"}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "21.json"
            with redirect_stdout(io.StringIO()):
                saved = save_hiddify_subscription(configs, path)
            self.assertEqual(saved, [str(path.with_suffix("") / "1.json"), str(path.with_suffix("") / "2.json")])
            self.assertFalse(path.exists())
            for index, filename in enumerate(saved):
                result = json.loads(Path(filename).read_text())
                self.assertIsInstance(result, dict)
                self.assertEqual(result["route"]["rules"], configs[index]["route"]["rules"])

    def test_invalid_array_does_not_write_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "21.json"
            with self.assertRaises(ConversionError):
                save_hiddify_subscription([sample_config(), {"outbounds": [{}]}], path)
            self.assertFalse(path.with_suffix("").exists())

    def test_single_json_file_saved_with_unicode_tags(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "1.json"
            with redirect_stdout(io.StringIO()):
                saved = save_hiddify_subscription(sample_config(), path)
            self.assertEqual(saved, [str(path)])
            self.assertIn("🇭🇰 Proxy", path.read_text())
            self.assertEqual(json.loads(path.read_text())["outbounds"][0]["type"], "selector")


if __name__ == "__main__":
    unittest.main()
