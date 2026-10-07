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
