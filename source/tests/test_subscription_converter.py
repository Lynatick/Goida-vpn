import base64
import ast
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from subscription_converter import ConversionError, convert_subscription, save_raw_subscription


USER_ID = "cbb3f877-d1fb-344c-87a9-d153bffd5484"


def encode(value):
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def vmess(**overrides):
    fields = {
        "add": "v35.hdacd.com", "port": "30835", "id": USER_ID,
        "aid": 2, "ps": "🇭🇰_HK_中国香港->🇫🇷_FR_法国", "net": "tcp"
    }
    fields.update(overrides)
    return "vmess://" + encode(json.dumps(fields, ensure_ascii=False))


class SubscriptionConversionTest(unittest.TestCase):
    def test_vmess_matches_requested_example(self):
        config, issues = convert_subscription(vmess())
        self.assertEqual(config, {
            "outbounds": [{
                "type": "vmess", "tag": "🇭🇰_HK_中国香港->🇫🇷_FR_法国 § 0",
                "server": "v35.hdacd.com", "server_port": 30835,
                "uuid": USER_ID, "security": "auto", "alter_id": 2,
                "authenticated_length": True, "packet_encoding": "xudp"
            }],
            "endpoints": []
        })
        self.assertFalse(issues)

    def test_base64_subscription_comments_and_unique_tags(self):
        text = "# comment\n" + vmess() + "\n// profile metadata\n" + vmess()
        encoded = encode(text)
        wrapped = "\n".join(encoded[i:i + 50] for i in range(0, len(encoded), 50))
        config, issues = convert_subscription(wrapped)
        self.assertEqual(len(config["outbounds"]), 2)
        self.assertNotEqual(config["outbounds"][0]["tag"], config["outbounds"][1]["tag"])
        self.assertFalse(issues)

    def test_vmess_websocket_preserves_tls_and_early_data(self):
        config, _ = convert_subscription(vmess(
            net="ws", host="cdn.example.com", path="/ws?ed=2048", tls="tls",
            sni="tls.example.com", alpn="h2,http/1.1", allowInsecure="false"
        ))
        outbound = config["outbounds"][0]
        self.assertEqual(outbound["transport"], {
            "type": "ws", "path": "/ws", "headers": {"Host": "cdn.example.com"},
            "max_early_data": 2048, "early_data_header_name": "Sec-WebSocket-Protocol"
        })
        self.assertEqual(outbound["tls"], {
            "enabled": True, "server_name": "tls.example.com",
            "insecure": False, "alpn": ["h2", "http/1.1"]
        })

    def test_vless_ipv6_reality_and_grpc(self):
        link = (
            f"vless://{USER_ID}@[2001:db8::1]:443?security=reality&pbk=public-key"
            "&sid=abcdef&fp=chrome&sni=example.com&type=grpc&serviceName=tunnel#Test"
        )
        config, _ = convert_subscription(link)
        outbound = config["outbounds"][0]
        self.assertEqual(outbound["server"], "2001:db8::1")
        self.assertEqual(outbound["transport"], {"type": "grpc", "service_name": "tunnel"})
        self.assertEqual(outbound["tls"]["reality"]["public_key"], "public-key")
        self.assertEqual(outbound["tls"]["utls"]["fingerprint"], "chrome")

    def test_trojan_password_and_explicit_false(self):
        config, _ = convert_subscription("trojan://p%40ss%3Aword@host.test:443?allowInsecure=0")
        outbound = config["outbounds"][0]
        self.assertEqual(outbound["password"], "p@ss:word")
        self.assertEqual(outbound["tls"], {"enabled": True, "insecure": False})

    def test_shadowsocks_supported_encodings_and_plugin(self):
        links = [
            "ss://" + encode("aes-256-gcm:pass:word") + "@host.test:8388#One",
            "ss://" + encode("aes-256-gcm:pass:word@host.test:8388") + "#Two",
            "ss://aes-256-gcm:pass%3Aword@host.test:8388#Three"
        ]
        for link in links:
            with self.subTest(link=link):
                config, _ = convert_subscription(link)
                outbound = config["outbounds"][0]
                self.assertEqual(outbound["method"], "aes-256-gcm")
                self.assertEqual(outbound["password"], "pass:word")
                self.assertEqual(outbound["server_port"], 8388)
        config, _ = convert_subscription(links[0].split("#")[0] + "?plugin=obfs-local%3Bobfs%3Dhttp")
        self.assertEqual(config["outbounds"][0]["plugin_opts"], "obfs=http")

    def test_legacy_shadowsocks_json(self):
        link = "ss://" + encode(json.dumps({
            "add": "host.test", "port": 8388, "scy": "aes-128-gcm", "id": "pass"
        }))
        config, _ = convert_subscription(link)
        self.assertEqual(config["outbounds"][0]["password"], "pass")

    def test_standard_base64_shadowsocks_containing_slash(self):
        encoded = base64.b64encode(b"aes-256-gcm:???@host.test:8388").decode()
        self.assertIn("/", encoded)
        config, _ = convert_subscription("ss://" + encoded)
        self.assertEqual(config["outbounds"][0]["password"], "???")

    def test_hysteria_tuic_and_anytls(self):
        links = [
            "hy2://user%3Apass@host.test?obfs=salamander&obfs-password=secret&sni=example.com",
            f"tuic://{USER_ID}:pass@host.test:443?congestion_control=bbr&udp_relay_mode=native",
            "anytls://password@host.test:443?sni=example.com"
        ]
        config, issues = convert_subscription("\n".join(links))
        self.assertFalse(issues)
        self.assertEqual([item["type"] for item in config["outbounds"]], ["hysteria2", "tuic", "anytls"])
        self.assertEqual(config["outbounds"][0]["password"], "user:pass")
        self.assertEqual(config["outbounds"][0]["server_port"], 443)
        self.assertEqual(config["outbounds"][1]["password"], "pass")

    def test_unsupported_transports_and_invalid_nodes_reported(self):
        text = "\n".join([
            vmess(), "vmess://invalid", f"vless://{USER_ID}@host.test:443?type=xhttp",
            f"vless://{USER_ID}@host.test:443?security=reality", "ssr://unsupported"
        ])
        config, issues = convert_subscription(text)
        self.assertEqual(len(config["outbounds"]), 1)
        self.assertEqual(sum(issues.values()), 4)
        self.assertIn("Неподдерживаемый транспорт: xhttp", issues)

    def test_invalid_input_does_not_overwrite_existing_raw_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "1.txt"
            path.write_text("existing data")
            for content in ("", "<html>404</html>", "vmess://broken"):
                with self.subTest(content=content), self.assertRaises(ValueError):
                    save_raw_subscription(content, path)
                self.assertEqual(path.read_text(), "existing data")

    def test_same_filename_utf8_json_and_existing_singbox_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "raw" / "1.txt"
            with redirect_stdout(io.StringIO()):
                config = save_raw_subscription(vmess(), path)
            text = path.read_text()
            self.assertIn("🇭🇰", text)
            self.assertEqual(json.loads(text), config)
            converted, _ = convert_subscription(text)
            self.assertEqual(converted, config)

    def test_main_saves_and_uploads_original_and_converted_file(self):
        module = ast.parse((Path(__file__).parents[1] / "main.py").read_text())
        main = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        original = "githubmirror/1.txt"
        raw = "raw/1.txt"
        save = Mock()
        upload = Mock()
        convert = Mock()
        namespace = {
            "GITHUB_TOKEN": "dummy-token", "REPO_NAME_1": "owner/repo",
            "URLS": ["source"], "LOCAL_PATHS": [original], "REMOTE_PATHS": [original],
            "fetch_data": Mock(return_value="data"), "save_to_local_file": save,
            "save_raw_subscription": convert, "upload_to_github": upload,
            "print_progress": Mock(), "print": Mock(), "os": os
        }
        exec(compile(ast.Module(body=[main], type_ignores=[]), "main.py", "exec"), namespace)
        namespace["main"]()
        save.assert_called_once_with(original, "data")
        convert.assert_called_once_with("data", raw)
        self.assertEqual([call.args for call in upload.call_args_list], [(original, original), (raw, raw)])
        upload.reset_mock()
        convert.side_effect = ConversionError("Unsupported source")
        namespace["main"]()
        upload.assert_called_once_with(original, original)


if __name__ == "__main__":
    unittest.main()
