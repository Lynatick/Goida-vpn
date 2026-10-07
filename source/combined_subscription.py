"""Combine numbered URI subscriptions into shared mirror, raw and Hiddify files."""

import argparse
import json
from pathlib import Path

from hiddify_subscription import build_hiddify_config
from subscription_converter import ConversionError, convert_subscription, decode_base64


def build_combined_subscriptions(root=".", source_paths=None):
    root = Path(root)
    sources = sorted(
        (path for path in (root / "githubmirror").glob("*.txt") if path.stem.isdigit()),
        key=lambda path: int(path.stem)
    ) if source_paths is None else [Path(path) for path in source_paths]
    links = {}
    for path in sources:
        text = path.read_text(encoding="utf-8-sig").strip()
        if not text:
            continue
        if "://" not in text and not text.startswith(("{", "[")):
            text = decode_base64(text).strip()
        if text.startswith(("{", "[")):
            raise ConversionError(
                f"{path}: полные JSON-конфигурации нельзя объединить в список URI "
                "без потери правил. Общие файлы не обновлены."
            )
        for line in text.splitlines():
            link = line.strip()
            if link and not link.startswith(("#", "//")):
                if "://" not in link:
                    raise ConversionError(f"{path}: некорректная строка подписки")
                links.setdefault(link, None)
    if not links:
        raise ConversionError("Нет URI для общей подписки")

    mirror = "\n".join(links) + "\n"
    config, issues = convert_subscription(mirror)
    hiddify = build_hiddify_config(config)
    # Build and validate every output before replacing existing files.
    outputs = {
        "githubmirror/all.txt": mirror,
        "raw/all.txt": json.dumps(config, ensure_ascii=False, indent=1) + "\n",
        "hiddify/all.json": json.dumps(hiddify, ensure_ascii=False, indent=1) + "\n"
    }
    for name, content in outputs.items():
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
    print(
        f"Общая подписка: источников {len(sources)}, уникальных URI {len(links)}, "
        f"серверов Hiddify {len(config['outbounds'])}, пропущено {sum(issues.values())}",
        flush=True
    )
    for reason, count in issues.items():
        print(f"  {reason}: {count}", flush=True)
    return list(outputs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Корень репозитория")
    args = parser.parse_args()
    build_combined_subscriptions(args.root)


if __name__ == "__main__":
    main()
