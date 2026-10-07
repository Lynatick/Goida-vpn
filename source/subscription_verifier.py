"""Sequential YouTube preflight before publishing subscriptions."""

import importlib.util
import json
from pathlib import Path
from urllib.parse import urlsplit

from hiddify_subscription import NON_PROXY_TYPES
from subscription_converter import ConversionError, convert_subscription, decode_base64, uri_outbound
from youtube_check import DEFAULT_CORE, DEFAULT_VIDEO, check_node


class SubscriptionVerifier:
    def __init__(self, core=DEFAULT_CORE, video=DEFAULT_VIDEO, timeout=15, report_dir="reports/preflight"):
        target = urlsplit(video)
        if timeout < 1 or target.scheme != "https" or target.hostname not in ("www.youtube.com", "youtube.com", "youtu.be"):
            raise ValueError("Нужны положительный тайм-аут и HTTPS-ссылка на ролик YouTube")
        if not Path(core).is_file():
            raise RuntimeError("Не найдено ядро Hiddify; укажите --core")
        if importlib.util.find_spec("yt_dlp") is None:
            raise RuntimeError("Установите зависимости из source/requirements-youtube.txt")
        self.core = str(Path(core).resolve())
        self.video = video
        self.timeout = timeout
        self.report_dir = Path(report_dir)

    def filter_subscription(self, content, source):
        text = content.strip().lstrip("\ufeff").strip()
        if "://" not in text and not text.startswith(("{", "[")):
            text = decode_base64(text).strip()
        native_json = text.startswith(("{", "["))
        rejected = 0
        if native_json:
            config, _ = convert_subscription(text)
            configs = config if isinstance(config, list) else [config]
            entries = []
            for item in configs:
                entries.extend((None, node) for node in item.get("outbounds", [])
                               if node.get("type") not in NON_PROXY_TYPES)
                entries.extend((None, node) for node in item.get("endpoints", []))
        else:
            entries = []
            for line in text.splitlines():
                link = line.strip()
                if not link or link.startswith(("#", "//")):
                    continue
                try:
                    entries.append((link, uri_outbound(link)))
                except (ValueError, TypeError, KeyError, AttributeError):
                    rejected += 1

        self.report_dir.mkdir(parents=True, exist_ok=True)
        report = self.report_dir / (Path(source).stem + ".jsonl")
        accepted = []
        passed = 0
        with report.open("w", encoding="utf-8") as file:
            for index, (link, node) in enumerate(entries, 1):
                print(f"{source}: проверка YouTube {index}/{len(entries)}…", flush=True)
                try:
                    result = check_node(node, self.core, self.video, self.timeout)
                except (ValueError, OSError):
                    result = {"status": "core_error", "reason": "Конфигурация не поддерживает изолированную проверку"}
                file.write(json.dumps({"index": index, "tag": node.get("tag", ""), **result}, ensure_ascii=False) + "\n")
                file.flush()
                if result["status"] == "media_received":
                    passed += 1
                    if link is not None:
                        accepted.append(link)
                print(f"{source}: {index}/{len(entries)} — {result['status']}; прошли {passed}", flush=True)
        print(f"{source}: прошли {passed}/{len(entries)}, некорректных URI {rejected}; отчёт {report}", flush=True)
        if not passed:
            raise ConversionError("Нет серверов с подтверждённым получением видеоданных YouTube")
        if native_json:
            if passed != len(entries):
                raise ConversionError("Полный JSON-профиль отклонён: не все серверы прошли проверку; правила не изменены")
            return text
        return "\n".join(dict.fromkeys(accepted)) + "\n"
