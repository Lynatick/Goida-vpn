Наведите курсор на блок со ссылкой и нажмите кнопку копирования в его правом верхнем углу.
Затем в Hiddify выберите **Новый профиль → Добавить из буфера обмена**.

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/1.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/2.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/3.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/4.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/5.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/6.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/7.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/8.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/9.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/10.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/11.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/12.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/13.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/14.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/15.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/16.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/17.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/18.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/19.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/20.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/21.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/22.json
```

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/23.json
```

Общие подписки всех источников:

- [Hiddify — все серверы](https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/all.json)
- [Исходные URI — все конфигурации](https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/githubmirror/all.txt)
- [Объединённый JSON sing-box](https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/raw/all.txt)

Общие файлы создаются при запуске `source/main.py`. Пересобрать их из локальных
источников без скачивания: `python3 source/combined_subscription.py`.
Повторяющиеся URI исключаются. Неподдерживаемые записи остаются в общем списке URI,
а при преобразовании в JSON пропускаются с отчётом. Полные JSON-конфигурации
с отдельными правилами маршрутизации не объединяются: сборка завершится ошибкой
и сохранит прежние общие файлы.

Проверка YouTube в Hiddify: обновите профиль, подключитесь и в разделе **Прокси**
выберите в группе `select` вариант **YouTube**. Эта группа проверяет соединение
с `https://www.youtube.com/generate_204` через серверы подписки и автоматически
выбирает сервер по задержке; интервал проверки — 3 минуты.
Это HTTP-тест доступности YouTube, а не проверка воспроизведения видео: ограничения
конкретных роликов, CDN `googlevideo.com` и запросы подтверждения аккаунта им не проверяются.
Обычный вариант `auto` остаётся доступен.
Описание встроенного теста: [URLTest sing-box](https://sing-box.sagernet.org/configuration/outbound/urltest/).

Проверка получения видеоданных через ядро Hiddify (macOS, Python 3.10+):

```bash
python3 -m pip install -r source/requirements-youtube.txt
python3 source/youtube_check.py --config hiddify/4.json --node 1 --count 3
```

Нужны установленный Hiddify и JavaScript runtime для yt-dlp (например, Node.js).
Скрипт использует ядро из `/Applications/Hiddify.app`, запускает временный локальный
прокси для каждого выбранного сервера и проверяет страницу тестового ролика,
получение адреса видеопотока и загрузку до 16 КиБ видео с `googlevideo.com`.
Группы `select`, `auto` и `YouTube` не учитываются в нумерации серверов.
Приложение Hiddify запускать не требуется; системный VPN и настройки прокси не меняются.

Другой ролик можно указать через `--video`, другое ядро — через `--core`.
Отчёт сохраняется в `reports/youtube.json` (не включается в Git).
`media_received` означает получение фрагмента MP4/WebM через выбранный прокси;
`connection_failed` — ошибку доступа к странице; `core_error` — ошибку запуска ядра;
`inconclusive` — сайт доступен, но видео не подтверждено (включая CAPTCHA,
ограничения ролика или ошибку yt-dlp). Тест не гарантирует воспроизведение всех
роликов и не измеряет скорость длительного просмотра.
Для извлечения адреса видеопотока используется [yt-dlp](https://github.com/yt-dlp/yt-dlp).

Обновление подписок теперь включает обязательную последовательную проверку
каждого сервера через ядро Hiddify до сохранения и отправки в GitHub:

```bash
python3 -m pip install -r source/requirements.txt
python3 source/main.py --local-only --timeout 15
```

Для отправки через GitHub API запустите без `--local-only`.
Параллельная обработка не используется. В новые файлы `githubmirror`, `raw` и
`hiddify` попадают только серверы со статусом `media_received`.
Ошибки соединения, запуска ядра и результаты `inconclusive` исключаются.
Если источник не прошёл проверку, его прежние файлы сохраняются и не отправляются
повторно; при этом общие файлы собираются только из источников, прошедших проверку
в текущем запуске. Ранее опубликованные файлы автоматически не удаляются.
Полные JSON-профили с маршрутами принимаются только при успешной проверке всех
серверов: их правила не обрезаются. Отчёт по каждому источнику сохраняется в
`reports/preflight/<номер>.jsonl`. Проверка большого числа серверов занимает много
времени; прогресс выводится после каждого сервера.
