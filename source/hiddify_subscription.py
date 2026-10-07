"""Build sing-box JSON subscriptions with manual and automatic server selection."""

import argparse
from copy import deepcopy
import json
from pathlib import Path

from subscription_converter import ConversionError, convert_subscription, validate_json_config


NON_PROXY_TYPES = {"direct", "block", "dns", "selector", "urltest"}
YOUTUBE_TEST_URL = "https://www.youtube.com/generate_204"


def build_hiddify_config(config):
    validate_json_config(config)
    result = deepcopy(config)
    outbounds = result.setdefault("outbounds", [])
    endpoints = result.setdefault("endpoints", [])
    if any("type" not in outbound for outbound in outbounds):
        raise ConversionError(
            "Для Hiddify нужен JSON sing-box с полем type. "
            "Готовый Xray/V2Ray JSON остаётся в raw; требуется отдельное "
            "преобразование его маршрутизации в sing-box."
        )

    used_tags = set()
    for item in outbounds + endpoints:
        tag = item.get("tag")
        if tag is not None:
            if not isinstance(tag, str) or not tag:
                raise ConversionError("В конфигурации указан некорректный тег")
            if tag in used_tags:
                raise ConversionError("В одной конфигурации повторяются теги")
            used_tags.add(tag)

    def new_tag(base):
        tag = base
        suffix = 1
        while tag in used_tags:
            tag = f"{base}-{suffix}"
            suffix += 1
        used_tags.add(tag)
        return tag

    candidates = []
    for index, item in enumerate(outbounds + endpoints):
        if not item.get("tag"):
            item["tag"] = new_tag(f"{item['type']}-{index}")
        if item["type"] not in NON_PROXY_TYPES:
            candidates.append(item["tag"])
    if not candidates:
        raise ConversionError("Нет серверов для подписки Hiddify")

    selector_tag = new_tag("select")
    auto_tag = new_tag("auto")
    youtube_tag = new_tag("YouTube")
    selector = {
        "type": "selector",
        "tag": selector_tag,
        "outbounds": [auto_tag, youtube_tag] + candidates,
        "default": auto_tag,
        "interrupt_exist_connections": True
    }
    automatic = {
        "type": "urltest",
        "tag": auto_tag,
        "outbounds": candidates,
        "url": "https://www.gstatic.com/generate_204",
        "interval": "3m",
        "tolerance": 50,
        "interrupt_exist_connections": True
    }
    youtube = {
        "type": "urltest",
        "tag": youtube_tag,
        "outbounds": candidates,
        "url": YOUTUBE_TEST_URL,
        "interval": "3m",
        "tolerance": 50,
        "interrupt_exist_connections": True
    }
    result["outbounds"] = [selector, automatic, youtube] + outbounds
    route = result.setdefault("route", {})
    if not isinstance(route, dict):
        raise ConversionError("Поле route должно быть объектом")
    route["final"] = selector_tag
    return result


def save_hiddify_subscription(config, path):
    """Save array members separately so each profile retains its own rules."""
    path = Path(path)
    if isinstance(config, list):
        if not config:
            raise ConversionError("JSON-массив пуст")
        profiles = [
            (path.with_suffix("") / f"{index}.json", build_hiddify_config(item))
            for index, item in enumerate(config, start=1)
        ]
    else:
        profiles = [(path, build_hiddify_config(config))]
    # Validate all array entries before creating or replacing any files.
    for destination, profile in profiles:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(profile, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(f"Подписка Hiddify сохранена в {destination}", flush=True)
    return [str(destination) for destination, _ in profiles]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="raw")
    parser.add_argument("--output-dir", default="hiddify")
    args = parser.parse_args()
    paths = sorted(
        path for path in Path(args.directory).iterdir()
        if path.is_file() and path.suffix in (".txt", ".json")
    )
    if not paths:
        parser.error("В каталоге нет файлов *.txt или *.json")
    failed = 0
    generated = 0
    for path in paths:
        destination = Path(args.output_dir) / (path.stem + ".json")
        try:
            config, _ = convert_subscription(path.read_text(encoding="utf-8-sig"))
            generated += len(save_hiddify_subscription(config, destination))
        except (ValueError, OSError) as error:
            failed += 1
            print(f"Не удалось создать подписку {destination}: {error}", flush=True)
    print(
        f"Обработано файлов: {len(paths) - failed}/{len(paths)}, "
        f"создано подписок Hiddify: {generated}.",
        flush=True
    )
    return int(failed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
