import os
import sys
import argparse
from getpass import getpass
import requests
from github import Github, GithubException
from datetime import datetime
import zoneinfo
from subscription_converter import save_raw_subscription
from hiddify_subscription import save_hiddify_subscription

# Определение времени по МСК
zone = zoneinfo.ZoneInfo("Europe/Moscow")
thistime = datetime.now(zone)
offset = thistime.strftime("%H:%M | %d.%m.%Y")

GITHUB_TOKEN = os.environ.get("MY_TOKEN") or os.environ.get("GITHUB_TOKEN")
REPO_NAME_1 = os.environ.get("GITHUB_REPOSITORY", "Lynatick/Goida-vpn")

# Если локальная папка не существует, создаём её
if not os.path.exists("githubmirror"):
    os.mkdir("githubmirror")

# Список URL и локальных/удалённых путей
URLS = [
    "https://istanbulsydneyhotel.com/blogs/site/sni.php?security=reality", #1
    "https://istanbulsydneyhotel.com/blogs/site/sni.php", #2
    "https://raw.githubusercontent.com/ermaozi/get_subscribe/main/subscribe/v2ray.txt", #3
    "https://raw.githubusercontent.com/acymz/AutoVPN/refs/heads/main/data/V2.txt", #4
    "https://raw.githubusercontent.com/AliDev-ir/FreeVPN/main/pcvpn",  #5
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/V2RAY_RAW.txt",  #6
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/All_Configs_Sub.txt",  #7
    "https://shadowmere.xyz/api/b64sub/",  #8
    "https://vpn.fail/free-proxy/v2ray",   #9
    "https://raw.githubusercontent.com/Proxydaemitelegram/Proxydaemi44/refs/heads/main/Proxydaemi44",  #10
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",   #11
    "https://raw.githubusercontent.com/mheidari98/.proxy/refs/heads/main/all",   #12
    "https://github.com/Kwinshadow/TelegramV2rayCollector/raw/refs/heads/main/sublinks/mix.txt",   #13
    "https://github.com/LalatinaHub/Mineral/raw/refs/heads/master/result/nodes",   #14
    "https://github.com/4n0nymou3/multi-proxy-config-fetcher/raw/refs/heads/main/configs/proxy_configs.txt",   #15
    "https://github.com/freefq/free/raw/refs/heads/master/v2",    #16
    "https://github.com/MhdiTaheri/V2rayCollector_Py/raw/refs/heads/main/sub/Mix/mix.txt", #17
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/All_Configs_Sub.txt", #18
    "https://github.com/MhdiTaheri/V2rayCollector/raw/refs/heads/main/sub/mix",   #19
    "https://raw.githubusercontent.com/mehran1404/Sub_Link/refs/heads/main/V2RAY-Sub.txt",  #20
    "https://raw.githubusercontent.com/shabane/kamaji/master/hub/merged.txt",   #21
    "https://raw.githubusercontent.com/wuqb2i4f/xray-config-toolkit/main/output/base64/mix-uri",   #22
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/refs/heads/main/v2ray_configs.txt",  #23
]

REMOTE_PATHS = [f"githubmirror/{i+1}.txt" for i in range(len(URLS))]
LOCAL_PATHS = [f"githubmirror/{i+1}.txt" for i in range(len(URLS))]


def fetch_data(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def save_to_local_file(path, content):
    with open(path, "w", encoding="utf-8") as file:
        file.write(content)
    print(f"Данные сохранены локально в {path}", flush=True)


def upload_to_github(local_path, remote_path):
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Файл {local_path} не найден.")

    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME_1)

    with open(local_path, "r", encoding="utf-8") as file:
        content = file.read()

    try:
        file_in_repo = repo.get_contents(remote_path)
        repo.update_file(
            path=remote_path,
            message=f"Обновление конфига по часовому поясу Европа/Москва: {offset}",
            content=content,
            sha=file_in_repo.sha
        )
        print(f"Файл {remote_path} обновлён.", flush=True)
    except GithubException as e:
        if e.status != 404:
            raise
        repo.create_file(
            path=remote_path,
            message=f"Первый коммит по часовому поясу Европа/Москва: {offset}",
            content=content
        )
        print(f"Файл {remote_path} создан.", flush=True)


def print_progress(completed, total):
    fraction = completed / total if total else 1
    filled = int(20 * fraction)
    bar = "#" * filled + "-" * (20 - filled)
    print(
        f"Обработано: [{bar}] {fraction:.0%} ({completed}/{total})",
        flush=True
    )


def main(local_only=False):
    global GITHUB_TOKEN

    if not local_only and not GITHUB_TOKEN:
        if not sys.stdin.isatty():
            raise RuntimeError(
                "Для ввода токена запустите скрипт в терминале или задайте "
                "MY_TOKEN / GITHUB_TOKEN в окружении."
            )
        try:
            GITHUB_TOKEN = getpass(
                f"Введите GitHub токен для {REPO_NAME_1} (ввод скрыт): "
            ).strip()
        except EOFError:
            raise RuntimeError("Ввод токена прерван.") from None
    if not local_only and not GITHUB_TOKEN:
        raise RuntimeError(
            "Токен не введён. Нужен GitHub токен с правом записи Contents "
            "в репозиторий " + REPO_NAME_1
        )
    total = len(URLS)
    completed = 0
    failed_sources = []
    print(f"Обновление {total} конфигов в {REPO_NAME_1}", flush=True)
    print_progress(completed, total)
    try:
        for index, (url, local_path, remote_path) in enumerate(
            zip(URLS, LOCAL_PATHS, REMOTE_PATHS), start=1
        ):
            print(f"\n[{index}/{total}] Скачивание {url}", flush=True)
            try:
                data = fetch_data(url)
                if not data.strip():
                    raise ValueError("Источник вернул пустые данные")
            except (requests.RequestException, ValueError) as error:
                failed_sources.append((url, local_path, str(error)))
                print(f"[{index}/{total}] Источник пропущен: {error}", flush=True)
                print_progress(index, total)
                continue
            print(f"[{index}/{total}] Сохранение {local_path}", flush=True)
            save_to_local_file(local_path, data)
            raw_path = os.path.join("raw", os.path.basename(local_path))
            hiddify_paths = []
            print(f"[{index}/{total}] Преобразование в {raw_path}", flush=True)
            try:
                config = save_raw_subscription(data, raw_path)
            except ValueError as error:
                print(
                    f"[{index}/{total}] JSON не создан для {raw_path}: {error}",
                    flush=True
                )
                raw_path = None
            if raw_path:
                hiddify_path = os.path.join(
                    "hiddify", os.path.splitext(os.path.basename(local_path))[0] + ".json"
                )
                try:
                    hiddify_paths = save_hiddify_subscription(config, hiddify_path)
                except ValueError as error:
                    print(
                        f"[{index}/{total}] Подписка Hiddify не создана для "
                        f"{hiddify_path}: {error}",
                        flush=True
                    )
            if not local_only:
                print(
                    f"[{index}/{total}] Отправка {remote_path} в GitHub",
                    flush=True
                )
                upload_to_github(local_path, remote_path)
                if raw_path:
                    print(f"[{index}/{total}] Отправка {raw_path} в GitHub", flush=True)
                    upload_to_github(raw_path, raw_path)
                for hiddify_path in hiddify_paths:
                    print(f"[{index}/{total}] Отправка {hiddify_path} в GitHub", flush=True)
                    upload_to_github(hiddify_path, hiddify_path)
            completed += 1
            print_progress(index, total)
    except Exception as e:
        print(
            f"Произошла ошибка: {e}. Завершено {completed}/{total} конфигов.",
            flush=True
        )
        raise
    action = "обновлено локально" if local_only else "отправлено"
    print(f"\nОбработка завершена: {action} {completed}/{total} конфигов.", flush=True)
    if failed_sources:
        print("Пропущенные источники и ожидаемые файлы:", flush=True)
        for url, local_path, error in failed_sources:
            name = os.path.basename(local_path)
            print(
                f"- {url}: {error}\n"
                f"  {local_path}; raw/{name}; hiddify/{os.path.splitext(name)[0]}.json",
                flush=True
            )
    if total and completed == 0:
        raise RuntimeError("Не удалось получить данные ни из одного источника.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Обновление конфигов VPN и подписок Hiddify")
    parser.add_argument(
        "--local-only", action="store_true",
        help="Скачать и преобразовать данные без токена и отправки через GitHub API"
    )
    main(local_only=parser.parse_args().local_only)
