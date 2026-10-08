"""Combine numbered URI subscriptions into shared mirror, raw and Hiddify files."""

import argparse
import json
from pathlib import Path

from hiddify_subscription import build_hiddify_config
from subscription_converter import ConversionError, convert_subscription, decode_base64
from subscription_report import save_subscription_report
from protocol_subscriptions import build_protocol_subscriptions


def build_combined_subscriptions(root="."):
    root = Path(root)
    sources = sorted(
        (path for path in (root / "githubmirror").glob("*.txt") if path.stem.isdigit()),
        key=lambda path: int(path.stem)
    )
    links = {}
    invalid_lines = 0
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
        skipped = 0
        for line in text.splitlines():
            link = line.strip()
            if link and not link.startswith(("#", "//")):
                if "://" not in link:
                    skipped += 1
                    continue
                links.setdefault(link, None)
        if skipped:
            invalid_lines += skipped
            print(f"{path}: пропущено некорректных строк без URI: {skipped}", flush=True)
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
        f"серверов Hiddify {len(config['outbounds'])}, "
        f"пропущено {invalid_lines + sum(issues.values())}",
        flush=True
    )
    protocol_paths, protocol_counts = build_protocol_subscriptions(config, root)
    report_paths = save_subscription_report(
        root, sources, config, invalid_lines + sum(issues.values()),
        protocol_counts=protocol_counts,
        protocol_uri_counts=json.loads((root / "protocol-stats.json").read_text())["uri_types"]
    )
    return list(outputs) + protocol_paths + report_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Корень репозитория")
    args = parser.parse_args()
    build_combined_subscriptions(args.root)


if __name__ == "__main__":
    main()
