"""Check YouTube media delivery through an isolated Hiddify core proxy."""

import argparse
from copy import deepcopy
import ctypes
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit

import requests

from hiddify_subscription import NON_PROXY_TYPES
from subscription_converter import convert_subscription


DEFAULT_CORE = "/Applications/Hiddify.app/Contents/Frameworks/hiddify-core.dylib"
DEFAULT_VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
SAMPLE_SIZE = 16384


def core_worker(core_path, config_path):
    core = ctypes.CDLL(core_path)
    core.parseCli.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)]
    core.parseCli.restype = ctypes.c_void_p
    core.freeString.argtypes = [ctypes.c_void_p]
    core.freeString.restype = None
    args = [b"hiddify-core", b"--disable-color", b"srun", b"-c", config_path.encode()]
    argv = (ctypes.c_char_p * len(args))(*args)
    result = core.parseCli(len(args), argv)
    if result:
        error = ctypes.string_at(result).decode()
        core.freeString(result)
        if error:
            return 1
    return 0


def proxy_config(node, port):
    node = deepcopy(node)
    if node.get("type") in NON_PROXY_TYPES or "server" not in node:
        raise ValueError("Нужен отдельный прокси-сервер sing-box")
    if node.get("detour"):
        raise ValueError("Для проверки цепочки detour нужен отдельный полный профиль")
    node["tag"] = "youtube-proxy"
    return {
        "log": {"disabled": True},
        "inbounds": [{"type": "mixed", "tag": "local-test", "listen": "127.0.0.1", "listen_port": port}],
        "outbounds": [node],
        "route": {"final": node["tag"]}
    }


def extract_metadata(proxy_url, video_url, timeout):
    command = [
        sys.executable, "-m", "yt_dlp", "--ignore-config", "--no-plugin-dirs",
        "--no-cache-dir", "--no-playlist", "--dump-single-json",
        "--proxy", proxy_url, "--socket-timeout", str(timeout),
        "--retries", "0", "--extractor-retries", "0",
        "--format", "worst[protocol=https][vcodec!=none]/worstvideo[protocol=https]"
    ]
    if shutil.which("node"):
        command.extend(["--js-runtimes", "node"])
    command.append(video_url)
    environment = {key: value for key, value in os.environ.items() if not key.lower().endswith("proxy")}
    result = subprocess.run(
        command, capture_output=True, text=True, timeout=timeout * 3, env=environment
    )
    if result.returncode:
        # Do not persist extractor output: it can contain signed media URLs.
        error = result.stderr.lower()
        if "bot" in error or "sign in" in error:
            reason = "YouTube требует подтверждение аккаунта или проверку CAPTCHA"
        elif "not available" in error or "unavailable" in error:
            reason = "Тестовый ролик недоступен на этом выходном IP"
        else:
            reason = "Не удалось получить видеопоток: ошибка сети или извлечения yt-dlp"
        raise ValueError(reason)
    return json.loads(result.stdout)


def read_video_sample(session, metadata, timeout):
    media_url = metadata.get("url", "")
    host = (urlsplit(media_url).hostname or "").lower()
    if urlsplit(media_url).scheme != "https" or not host.endswith(".googlevideo.com"):
        raise ValueError("Не получена HTTPS-ссылка на видеопоток googlevideo.com")
    if metadata.get("vcodec") in (None, "none"):
        raise ValueError("Получен формат без видеодорожки")
    headers = dict(metadata.get("http_headers") or {})
    headers["Range"] = f"bytes=0-{SAMPLE_SIZE - 1}"
    with session.get(media_url, headers=headers, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        if not (content_type.startswith("video/") or content_type == "application/octet-stream"):
            raise ValueError("CDN вернул страницу вместо видеоданных")
        sample = next(response.iter_content(chunk_size=SAMPLE_SIZE), b"")
        mp4 = len(sample) >= 12 and sample[4:8] in (b"ftyp", b"styp")
        webm = sample.startswith(b"\x1a\x45\xdf\xa3")
        if not (mp4 or webm):
            raise ValueError("Не распознан заголовок видеоконтейнера MP4/WebM")
        return len(sample)


def check_proxy(proxy_url, video_url, timeout):
    result = {"site_accessible": False, "status": "inconclusive", "media_bytes": 0}
    with requests.Session() as session:
        # Never use the system proxy or bypass this proxy via NO_PROXY.
        session.trust_env = False
        session.proxies = {"http": proxy_url, "https": proxy_url}
        try:
            with session.get(video_url, timeout=timeout, stream=True) as response:
                response.raise_for_status()
                result["site_accessible"] = True
        except requests.RequestException:
            result.update(status="connection_failed", reason="Страница YouTube недоступна через выбранный прокси")
            return result
        try:
            metadata = extract_metadata(proxy_url, video_url, timeout)
            result["video_id"] = metadata.get("id")
            result["media_bytes"] = read_video_sample(session, metadata, timeout)
            result["status"] = "media_received"
        except subprocess.TimeoutExpired:
            result["reason"] = "Истекло время получения данных ролика"
        except ValueError as error:
            result["reason"] = str(error)
        except (requests.RequestException, OSError):
            result["reason"] = "Сайт доступен, но получение видеоданных не подтверждено (CDN, yt-dlp или ограничения YouTube)"
        return result


def check_node(node, core_path, video_url, timeout):
    # Bind only loopback and never install a TUN or change the system proxy.
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    config = proxy_config(node, port)
    with tempfile.TemporaryDirectory(prefix="goida-youtube-") as directory:
        path = Path(directory) / "config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        path.chmod(0o600)
        if Path(core_path).suffix in (".dylib", ".dll", ".so"):
            command = [sys.executable, str(Path(__file__).resolve()), "--core-worker", core_path, str(path)]
        else:
            command = [core_path, "srun", "-c", str(path)]
        process = subprocess.Popen(command, cwd=directory, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    return {"status": "core_error", "reason": "Ядро Hiddify не приняло конфигурацию", "site_accessible": False, "media_bytes": 0}
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                return {"status": "core_error", "reason": "Ядро не запустило локальный прокси", "site_accessible": False, "media_bytes": 0}
            return check_proxy(f"http://127.0.0.1:{port}", video_url, timeout)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="hiddify/4.json")
    parser.add_argument("--core", default=DEFAULT_CORE, help="Библиотека или исполняемый файл ядра Hiddify")
    parser.add_argument("--node", type=int, default=1, help="Номер сервера (начиная с 1, группы не учитываются)")
    parser.add_argument("--count", type=int, default=1, help="Количество последовательных серверов для проверки")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--video", default=DEFAULT_VIDEO)
    parser.add_argument("--output", default="reports/youtube.json")
    args = parser.parse_args()
    if min(args.node, args.count, args.timeout) < 1:
        parser.error("Номер, количество и тайм-аут должны быть положительными")
    video = urlsplit(args.video)
    if video.scheme != "https" or video.hostname not in ("www.youtube.com", "youtube.com", "youtu.be"):
        parser.error("Укажите HTTPS-ссылку на ролик YouTube")
    if not Path(args.core).is_file():
        parser.error("Ядро Hiddify не найдено; укажите --core")
    if importlib.util.find_spec("yt_dlp") is None:
        parser.error("Установите зависимости: python -m pip install -r source/requirements-youtube.txt")
    config, _ = convert_subscription(Path(args.config).read_text(encoding="utf-8-sig"))
    if isinstance(config, list):
        parser.error("Выберите отдельную полную конфигурацию, а не JSON-массив")
    nodes = [node for node in config.get("outbounds", []) if node.get("type") not in NON_PROXY_TYPES]
    if not nodes or any("type" not in node for node in nodes):
        parser.error("Нужны прокси-серверы в формате sing-box")
    if args.node > len(nodes):
        parser.error(f"В файле только {len(nodes)} серверов")
    results = []
    for index, node in enumerate(nodes[args.node - 1:args.node - 1 + args.count], args.node):
        print(f"Проверка сервера {index}/{len(nodes)} через ядро Hiddify…", flush=True)
        try:
            result = check_node(node, str(Path(args.core).resolve()), args.video, args.timeout)
        except (ValueError, OSError):
            result = {"status": "core_error", "reason": "Не удалось запустить выбранную конфигурацию", "site_accessible": False, "media_bytes": 0}
        result.update(node_index=index, tag=node.get("tag", ""), checked_at=datetime.now(timezone.utc).isoformat())
        results.append(result)
        print(f"Сервер {index}: {result['status']}, видеоданных {result['media_bytes']} байт", flush=True)
        report = {"config": args.config, "video": args.video, "results": results}
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Отчёт: {args.output}", flush=True)
    return 0 if any(item["status"] == "media_received" for item in results) else 1


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--core-worker":
        raise SystemExit(core_worker(sys.argv[2], sys.argv[3]))
    raise SystemExit(main())
