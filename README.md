<div align="center">
  <span style="display: inline-block; width: 33.3%; text-align: left;">
    <a href="https://www.youtube.com/@avencores/" target="_blank">
      <img src="https://github.com/user-attachments/assets/338bcd74-e3c3-4700-87ab-7985058bd17e" alt="YouTube" height="40">
    </a>
  </span>
  <span style="display: inline-block; width: 33.3%; text-align: center;">
    <a href="https://t.me/avencoresyt" target="_blank">
      <img src="https://github.com/user-attachments/assets/939f8beb-a49a-48cf-89b9-d610ee5c4b26" alt="Telegram" height="40">
    </a>
  </span>
  <span style="display: inline-block; width: 33.3%; text-align: right;">
    <a href="https://vk.com/avencoresvk" target="_blank">
      <img src="https://github.com/user-attachments/assets/dc109dda-9045-4a06-95a5-3399f0e21dc4" alt="VK" height="40">
    </a>
  </span>
  </span>
  <span style="display: inline-block; width: 33.3%; text-align: right;">
    <a href="https://dzen.ru/avencores" target="_blank">
      <img src="https://github.com/user-attachments/assets/bd55f5cf-963c-4eb8-9029-7b80c8c11411" alt="Dzen" height="40">
    </a>
  </span>
</div>

</div>

# 🎦 Видео гайд по установке и решению проблем

![maxresdefault](https://github.com/user-attachments/assets/e36e2351-3b1a-4b90-87f7-cafbc74f238c)

<div align="center">

> ⚠️ **Внимание!** Для iOS и iPadOS актуален только текстовый гайд ниже. Видео гайд актуален только для Android, Android TV, Windows, Linux, MacOS.

[**Смотреть на YouTube**](https://youtu.be/sagz2YluM70)  

[**Смотреть на Dzen**](https://dzen.ru/video/watch/680d58f28c6d3504e953bd6d)  

[**Смотреть на VK Video**](https://vk.com/video-200297343_456239303)

[**Смотреть в Telegram**](https://t.me/avencoreschat/56595)

</div>


## Обновление конфигов в своём репозитории

Скрипт `source/main.py` сохраняет данные в `githubmirror/` и отправляет их в
`Lynatick/Goida-vpn`. Для другого репозитория задайте `GITHUB_REPOSITORY`
в формате `владелец/репозиторий`. Файлы публикуются в его ветку по умолчанию.

Установите зависимости и запустите скрипт из корня проекта:

```bash
python3 -m pip install -r source/requirements.txt
export GITHUB_REPOSITORY="Lynatick/Goida-vpn"
# Если токен не задан в окружении, скрипт запросит его в терминале.
python3 source/main.py
```

Для скачивания и преобразования файлов без GitHub-токена и отправки через API:

```bash
python3 source/main.py --local-only
```

После этого результаты можно отправить обычным Git-коммитом. Недоступные или
пустые источники пропускаются, прежние локальные файлы сохраняются, а в конце
выводится список ошибок и ожидаемых путей `githubmirror`, `raw` и `hiddify`.

Токену нужен доступ к выбранному репозиторию и разрешение **Contents: Read and write**.
Ввод токена скрыт; введённый токен используется только на время запуска и не сохраняется
на диск. Если задан `MY_TOKEN` или `GITHUB_TOKEN`, запрос ввода не появляется.
Не добавляйте токен в исходный код. В GitHub Actions переменная `GITHUB_REPOSITORY`
уже содержит текущий репозиторий; передайте токен через `MY_TOKEN` или `GITHUB_TOKEN`.

При обновлении скрипт также преобразует URI-подписки в JSON для sing-box с полями
`outbounds` и `endpoints`. Результат сохраняется и отправляется в каталог `raw`
с тем же именем: например, `githubmirror/1.txt` → `raw/1.txt`.
Файл сохраняет расширение `.txt`, но содержит JSON в UTF-8.

Поддерживаются обычные списки URI и подписки в Base64: VMess, VLESS, Trojan,
Shadowsocks, Hysteria2 (`hy2`), TUIC и AnyTLS. TLS, Reality и поддерживаемые
транспорты переносятся в JSON. Неподдерживаемые протоколы и транспорты (например,
SSR, mKCP и XHTTP), а также повреждённые записи пропускаются с отчётом о причинах.
Если пригодных подключений нет, существующий файл в `raw` не перезаписывается.
Формат полей описан в [документации sing-box](https://sing-box.sagernet.org/configuration/outbound/).

Готовые JSON-объекты и JSON-массивы полных конфигураций sing-box и Xray/V2Ray
сохраняются в `raw` в исходной структуре, включая ключи, параметры Reality,
правила `route`/`routing`, DNS, входящие подключения и теги. Это также работает
для JSON-подписок, закодированных в Base64. Элементы массива не объединяются,
чтобы разные правила и одинаковые теги из отдельных конфигураций не конфликтовали.
Готовый JSON Xray/V2Ray сохраняет свой формат и не преобразуется в sing-box.
Проверяется структура контейнера; пригодность настроек для конкретной версии
клиента следует проверять самим клиентом. Если массив содержит повреждённую
конфигурацию, файл не перезаписывается частично.

Уже скачанные файлы можно преобразовать без токена и запросов к сети:

```bash
python3 source/subscription_converter.py
```

Для другого каталога: `python3 source/subscription_converter.py githubmirror --output-dir raw`.

### Подписки для Hiddify

Скрипт обновления также создаёт и отправляет JSON-подписки sing-box в `hiddify`:
например, `raw/1.txt` → `hiddify/1.json`. В них есть группа `select` для ручного
выбора сервера и `auto` (`urltest`) для автоматического выбора по задержке.
Автоматический выбор включён по умолчанию, проверка выполняется каждые 3 минуты.
Проверку серверов выполняет клиент Hiddify после подключения, а не конвертер.

Для формирования подписок из уже скачанных JSON-файлов без сети и токена:

```bash
python3 source/hiddify_subscription.py
```

После публикации файлов в GitHub добавьте в Hiddify новый профиль по ссылке:

```text
https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/1.json
```

Поддерживается также ссылка быстрого импорта:

```text
hiddify://import/https://raw.githubusercontent.com/Lynatick/Goida-vpn/main/hiddify/1.json#Goida-1
```

При наличии массива полных конфигураций создаются отдельные подписки
`hiddify/<имя>/1.json`, `2.json` и т. д. Правила маршрутизации и параметры TLS/Reality
остаются в своих конфигурациях. Маршрут по умолчанию (`route.final`) направляется
в группу ручного/автоматического выбора. Исходные файлы в `raw` сохраняют все
первоначальные настройки. Теги новых групп получают суффиксы при совпадениях
с существующими тегами.

Готовый JSON Xray/V2Ray сохраняется в `raw`, но не выдаётся за JSON sing-box:
для создания его подписки Hiddify нужно отдельно преобразовать настройки и
маршрутизацию в sing-box или использовать исходные URI-ссылки.
Форматы импорта описаны в [документации Hiddify](https://github.com/hiddify/hiddify-app/wiki/URL-Scheme).

---
<details>

<summary>👩‍💻 Исходный код для генерации вечно актуальных конфигов</summary>

Ссылка на исходный код - [Ссылка](https://github.com/Lynatick/Goida-vpn/tree/main/source)

</details>


---
<details>

<summary>📋 Общий список всех вечно актуальных конфигов</summary>

1) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/1.txt`
2) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/2.txt`
3) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/3.txt`
4) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/4.txt`
5) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/5.txt`
6) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/6.txt`
7) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/7.txt`
8) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/8.txt`
9) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/9.txt`
10) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/10.txt`
11) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/11.txt`
12) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/12.txt`
13) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/13.txt`
14) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/14.txt`
15) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/15.txt`
16) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/16.txt`
17) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/17.txt`
18) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/18.txt`
19) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/19.txt`
20) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/20.txt`
21) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/21.txt`
22) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/22.txt`
23) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/23.txt`

🔗 [Ссылка на QR-коды вечно актуальных конфигов](https://github.com/AvenCores/goida-vpn-configs/tree/main/qr-codes)
</details>


---
<details>

<summary>📱 Гайд для Android</summary>

**1.** Скачиваем **v2rayNG** - [Ссылка](https://github.com/2dust/v2rayNG/releases/download/1.10.7/v2rayNG_1.10.7_universal.apk)

**2.** Копируем в буфер обмена: 

 - [ ] **Вечно актуальные**

1) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/1.txt`
2) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/2.txt`
3) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/3.txt`
4) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/4.txt`
5) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/5.txt`
6) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/6.txt`
7) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/7.txt`
8) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/8.txt`
9) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/9.txt`
10) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/10.txt`
11) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/11.txt`
12) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/12.txt`
13) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/13.txt`
14) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/14.txt`
15) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/15.txt`
16) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/16.txt`
17) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/17.txt`
18) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/18.txt`
19) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/19.txt`
20) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/20.txt`
21) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/21.txt`
22) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/22.txt`
23) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/23.txt`

**3.** Заходим в приложение **v2rayNG** и в правом верхнем углу нажимаем на ➕, а затем выбираем **Импорт из буфера обмена**.
   
**4.** Нажимаем **справа сверху на три точки**, а затем **Проверка профилей группы**, после окончания проверки в этом же меню нажмите на **Сортировка по результатам теста**. 

**5.** Выбираем нужный вам сервер и затем нажимаем на кнопку ▶️ в правом нижнем углу.

</details>

<details>

<summary>📺 Гайд для Android TV</summary>

**1.** Скачиваем **v2rayNG** - [Ссылка](https://github.com/2dust/v2rayNG/releases/download/1.10.7/v2rayNG_1.10.7_universal.apk)

**2.** Скачиваем **QR-коды** вечно актуальных конфигов - [Ссылка](https://github.com/AvenCores/goida-vpn-configs/tree/main/qr-codes)

**3**. Заходим в приложение **v2rayNG** и в правом верхнем углу нажимаем на ➕, а затем выбираем **Импорт из QR-кода**, выбираем картинку нажав на иконку фото в правом верхнем углу.

**4.** Нажимаем **справа сверху на три точки**, а затем **Проверка профилей группы**, после окончания проверки в этом же меню нажмите на **Сортировка по результатам теста**. 

**5.** Выбираем нужный вам сервер и затем нажимаем на кнопку ▶️ в правом нижнем углу.

</details>

<details>

<summary>⚠ Если нету интернета при подключении к VPN в v2rayNG</summary>

Ссылка на видео с демонстрацией фикса - [Ссылка](https://t.me/avencoreschat/25254)

</details>

<details>

<summary>⚠ Если не появились конфиги при добавлении VPN в v2rayNG</summary>

**1.** Нажмите на **три полоски** в **левом верхнем углу**.

**2.** Нажимаем на кнопку **Группы**.

**3.** Нажимаем на **иконку кружка со стрелкой** в **верхнем правом углу** и дожидаемся окончания обновления.

</details>

<details>

<summary>⚠ Фикс ошибки "Cбой проверки интернет-соединения: net/http: 12X handshake timeout"</summary>

**1.** На рабочем столе зажимаем на иконке **v2rayNG** и нажимаем на пункт **О приложении**.

**2.** Нажимаем на кнопку **Остановить** и заново запускаем **v2rayNG**.

</details>

<details>

<summary>🔄 Обновление конфигов в v2rayNG</summary>

**1.** Нажимаем на **иконку трех полосок** в **левом верхнем углу**.

**2.** Выбираем вкладку **Группы**.

**3.** Нажимаем на **иконку кружка со стрелкой** в **правом верхнем углу**.

</details>


---
<details>

<summary>🖥 Гайд для Windows, Linux</summary>

**1.** Скачиваем **NekoRay** - [Windows 10/11](https://github.com/Mahdi-zarei/nekoray/releases/download/4.3.5/nekoray-4.3.5-2025-05-16-windows64.zip) / [Windows 7](https://github.com/parhelia512/nekoray-win7/releases/download/4.3.4/nekoray-4.3.4-2025-04-23-windows64.zip) / [Linux](https://github.com/Mahdi-zarei/nekoray/releases/download/4.3.4/nekoray-4.3.4-2025-04-23-linux64.zip)

**2.** Копируем в буфер обмена: 

 - [ ] **Вечно актуальные**

1) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/1.txt`
2) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/2.txt`
3) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/3.txt`
4) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/4.txt`
5) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/5.txt`
6) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/6.txt`
7) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/7.txt`
8) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/8.txt`
9) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/9.txt`
10) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/10.txt`
11) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/11.txt`
12) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/12.txt`
13) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/13.txt`
14) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/14.txt`
15) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/15.txt`
16) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/16.txt`
17) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/17.txt`
18) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/18.txt`
19) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/19.txt`
20) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/20.txt`
21) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/21.txt`
22) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/22.txt`
23) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/23.txt`

**3.** Нажимаем на **Сервер**, а затем **Импортировать из буфера**.

**4.** Наживаем на **URL Test** в правом верхнем углу и дожидаемся конца теста.

**5.** Выделяем все конфиги комбинацией клавиш **Ctrl + A**, нажимаем **Профили** в верхнем меню, а затем **Сделать тест выбранного URL** и дожидаемся конца теста.

**6.** Выбираем тест с наименьшим **Ping**, а затем нажимаем **ЛКМ** и **Запустить**.

</details>

<details>

<summary>⚠ Исправляем ошибку MSVCP и VCRUNTIME на Windows 10/11</summary>

**1.** Нажимаем **Win+R** и пишем **control**.

**2.** Выбираем **Программы и компоненты**.

**3.** В поиск (справа сверху) пишем слово **Visual** и удалям все что касается **Microsoft Visual**.

**4.** Скачиваем архив и распаковываем - [Ссылка](https://dl.comss.org/download/Visual-C-Runtimes-All-in-One-Jun-2025.zip)

**5.** Запускаем от *имени Администратора* **install_bat.all** и ждем пока все установиться.

</details>

<details>

<summary>🔄 Обновление конфигов в NekoRay</summary>

**1.** Нажимаем на кнопку **Настройки**.

**2.** Выбираем **Группы**.

**3.** Нажимаем на кнопку **Обновить все подписки**.

</details>


---
<details>

<summary>☎ Гайд для iOS, iPadOS</summary>

**1.** Скачиваем **V2Box - V2ray Client** - [Ссылка](https://apps.apple.com/ru/app/v2box-v2ray-client/id6446814690)

**2.** Копируем в буфер обмена:

 - [ ] **Вечно актуальные**

1) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/1.txt`
2) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/2.txt`
3) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/3.txt`
4) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/4.txt`
5) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/5.txt`
6) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/6.txt`
7) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/7.txt`
8) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/8.txt`
9) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/9.txt`
10) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/10.txt`
11) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/11.txt`
12) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/12.txt`
13) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/13.txt`
14) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/14.txt`
15) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/15.txt`
16) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/16.txt`
17) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/17.txt`
18) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/18.txt`
19) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/19.txt`
20) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/20.txt`
21) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/21.txt`
22) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/22.txt`
23) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/23.txt`

**3.** Заходим в приложение **V2Box - V2ray Client** и переходим во вкладку **Config**, нажимаем на плюсик в правом верхнем углу, затем - **Добавить подписку**, вводим любое **Название** и вставляем ссылку на конфиг в поле **URL**.

**4.** После добавления конфига дожидаемся окончания проверки и выбираем нужный, просто нажав на его название.

**5.** В нижней панели программы нажимаем кнопку **Подключиться**.

</details>

<details>

<summary>🔄 Обновление конфигов в V2Box - V2ray Client</summary>

**1.** Переходим во вкладку **Config**.

**2.** Нажимаем на иконку обновления слева от названия группы подписки.

</details>


---
<details>

<summary>💻 Гайд для MacOS</summary>

**1.** Скачиваем **Hiddify** - [Ссылка](https://github.com/hiddify/hiddify-app/releases/latest/download/Hiddify-MacOS.dmg)

**2.** Нажимаем **Новый профиль**.

**3.** Копируем в буфер обмена:

 - [ ] **Вечно актуальные**

1) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/1.txt`
2) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/2.txt`
3) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/3.txt`
4) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/4.txt`
5) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/5.txt`
6) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/6.txt`
7) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/7.txt`
8) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/8.txt`
9) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/9.txt`
10) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/10.txt`
11) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/11.txt`
12) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/12.txt`
13) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/13.txt`
14) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/14.txt`
15) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/15.txt`
16) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/16.txt`
17) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/17.txt`
18) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/18.txt`
19) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/19.txt`
20) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/20.txt`
21) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/21.txt`
22) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/22.txt`
23) `https://github.com/Lynatick/Goida-vpn/raw/refs/heads/main/githubmirror/23.txt`

**4.** Нажимаем на кнопку **Добавить из буфера обмена**.
   
**5.** Перейдите в **Настройки**, измените **Вариант маршрутизации** на **Индонезия**.

**6.** Нажмите в левом верхнем меню на иконку настроек и выберите **VPN сервис**.

**7.** Включаем **VPN** нажав на иконку по середине. 

**8.** Для смены сервера включите **VPN** и перейдите во вкладку **Прокси**.

</details>

<details>

<summary>🔄 Обновление конфигов в Hiddify</summary>

**1.** Заходим в приложение **Hiddify** и выбираем нужный вам профиль.

**2.** Нажимаем **слева от названия профиля на иконку обновления**.

</details>

---
# 💰 Поддержать автора
+ **SBER**: `2202 2050 7215 4401`
