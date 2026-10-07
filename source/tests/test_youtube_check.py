from copy import deepcopy
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from youtube_check import check_proxy, extract_metadata, proxy_config, read_video_sample


class YoutubeCheckTest(unittest.TestCase):
    def test_isolated_core_config_has_no_direct_fallback_or_tun(self):
        node = {"type": "trojan", "tag": "original", "server": "test.example", "server_port": 443, "password": "secret"}
        original = deepcopy(node)
        config = proxy_config(node, 12345)
        self.assertEqual(node, original)
        self.assertEqual(config["inbounds"][0]["listen"], "127.0.0.1")
        self.assertEqual(config["inbounds"][0]["type"], "mixed")
        self.assertEqual(len(config["outbounds"]), 1)
        self.assertEqual(config["route"]["final"], config["outbounds"][0]["tag"])
        with self.assertRaises(ValueError):
            proxy_config(dict(node, detour="other-proxy"), 12345)

    def test_extractor_uses_explicit_proxy_without_environment_bypass(self):
        with patch("youtube_check.subprocess.run") as run, patch.dict("os.environ", {"NO_PROXY": "*", "HTTPS_PROXY": "http://other"}):
            run.return_value = subprocess.CompletedProcess([], 0, stdout='{"id":"video"}', stderr="")
            extract_metadata("http://127.0.0.1:12345", "https://www.youtube.com/watch?v=test", 5)
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("--proxy") + 1], "http://127.0.0.1:12345")
            self.assertNotIn("NO_PROXY", run.call_args.kwargs["env"])
            self.assertNotIn("HTTPS_PROXY", run.call_args.kwargs["env"])

    def test_video_sample_requires_media_container_not_just_http_success(self):
        session = MagicMock()
        response = session.get.return_value.__enter__.return_value
        response.headers = {"Content-Type": "video/mp4"}
        response.iter_content.return_value = iter([b"\x00\x00\x00\x18ftypisom"])
        metadata = {"url": "https://test.googlevideo.com/videoplayback?secret=signed", "vcodec": "avc1"}
        self.assertEqual(read_video_sample(session, metadata, 5), 12)
        self.assertEqual(session.get.call_args.kwargs["headers"]["Range"], "bytes=0-16383")
        response.iter_content.return_value = iter([b"<html>denied</html>"])
        with self.assertRaises(ValueError):
            read_video_sample(session, metadata, 5)
        response.headers = {"Content-Type": "text/html"}
        with self.assertRaises(ValueError):
            read_video_sample(session, metadata, 5)

    def test_site_success_without_video_is_inconclusive(self):
        with patch("youtube_check.requests.Session") as factory, patch("youtube_check.extract_metadata", side_effect=ValueError("CAPTCHA")):
            session = factory.return_value.__enter__.return_value
            result = check_proxy("http://127.0.0.1:12345", "https://www.youtube.com/watch?v=test", 5)
            self.assertTrue(result["site_accessible"])
            self.assertEqual(result["status"], "inconclusive")
            self.assertEqual(result["media_bytes"], 0)
            self.assertFalse(session.trust_env)

    def test_video_success_report_does_not_include_signed_media_url(self):
        metadata = {"id": "test", "url": "https://test.googlevideo.com/?token=private"}
        with patch("youtube_check.requests.Session"), patch("youtube_check.extract_metadata", return_value=metadata), patch("youtube_check.read_video_sample", return_value=16384):
            result = check_proxy("http://127.0.0.1:12345", "https://www.youtube.com/watch?v=test", 5)
            self.assertEqual(result["status"], "media_received")
            self.assertEqual(result["media_bytes"], 16384)
            self.assertNotIn("private", str(result))


if __name__ == "__main__":
    unittest.main()
