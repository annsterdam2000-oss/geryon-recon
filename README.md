# OSINT Panel

Локальная распределённая OSINT-система для сбора информации из открытых источников.

## Что это

Инструмент для OSINT-разведки: сервер раздаёт задачи агентам-воркерам, результаты собираются в веб-панели. Работает локально, внешние серверы не нужны.

## Архитектура

- **server/** — FastAPI-сервер, оркестратор задач
- **agent/** — воркеры, выполняют задачи
- **panel/** — веб-панель управления

## Модули

| Модуль       | Что собирает                                          |
| ------------ | ----------------------------------------------------- |
| `email`      | MX, A-записи, Gravatar                                |
| `email_reg`  | где email зарегистрирован (holehe)                    |
| `domain`     | WHOIS, DNS, поддомены, SSL, HTTP                      |
| `username`   | 35+ сайтов через распределённые подзадачи             |
| `ip`         | гео, ASN, PTR, RIR-whois                              |
| `phone`      | оператор, регион, тип линии                           |
| `person`     | поиск по ФИО в открытых источниках                    |

## Возможности

- Распределённая обработка задач (несколько агентов параллельно)
- Подзадачи для длинных операций (`username` разворачивается в 35 http-проверок)
- Уведомления в Discord о завершённых задачах
- SQLite — история задач и ботов сохраняется между запусками
- Веб-панель с прогресс-барами и фильтрами

## Зависимости

```bash
pip install -r requirements.txt
```

## Запуск сервера

```bash
cd server
python server.py
```

## Что должно быть в логе

```text
[*] startup: init_db()
[+] DB initialized: C:\projects\osint\server\osint.db
[*] startup: load_from_db()
[+] loaded 0 bots, 0 tasks from DB
[*] startup: done
INFO:     Uvicorn running on http://127.0.0.1:5555
```

## Запуск агентов

Открой второй терминал:

```bash
cd agent
python agent.py --count N
```

Где `N` — количество агентов.

## Что должно быть в логе агентов

```text
[+] registered as a1b2c3d4 modules=['email', 'email_reg', 'domain', 'http_check', 'ip', 'phone', 'person']
[+] registered as e5f6g7h8 modules=[...]
[+] запущено 5 агентов
```

## Как открыть панель

Открой браузер и перейди по адресу:

```text
http://127.0.0.1:5555
```

## Как пользоваться

1. Выбери задачу из списка:
   - `email`
   - `email_reg`
   - `domain`
   - `username`
   - `ip`
   - `phone`
   - `person` (ФИО)
2. Введи цель
3. Дождись результата в панели

## Примеры целей

| Тип         | Пример            |
| ----------- | ----------------- |
| email       | test@gmail.com    |
| email_reg   | test@gmail.com    |
| domain      | github.com        |
| username    | durov             |
| ip          | 8.8.8.8           |
| phone       | +79161234567      |
| person      | Павел Дуров       |

## Уведомления в Discord (опционально)

1. Создай Webhook в Discord:
   правой кнопкой по каналу → **Edit Channel** → **Integrations** → **Webhooks** → **New Webhook**.
   Скопируй URL.

2. Скопируй `server/.env.example` в `server/.env`:

   ```bash
   cd server
   copy .env.example .env
   ```

3. Открой `.env` и вставь Webhook URL:

   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

4. Перезапусти сервер.

Если `.env` не настроен — уведомления не приходят, но всё остальное работает.

## Структура проекта

```text
osint/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── server/
│   ├── server.py
│   ├── config.py
│   ├── db.py
│   ├── state.py
│   ├── logic.py
│   ├── notify.py
│   ├── sites.py
│   ├── models.py
│   ├── .env.example
│   └── routes/
│       ├── agent.py
│       └── panel.py
├── agent/
│   ├── agent.py
│   ├── client.py
│   └── modules/
│       ├── email.py
│       ├── email_reg.py
│       ├── domain.py
│       ├── http_check.py
│       ├── ip.py
│       ├── phone.py
│       └── person.py
└── panel/
    ├── panel.html
    ├── panel.js
    ├── style.css
    └── modules/
        ├── bots.js
        ├── tasks.js
        ├── details.js
        ├── utils.js
        └── renders/
            ├── email.js
            ├── email_reg.js
            ├── domain.js
            ├── username.js
            ├── ip.js
            ├── phone.js
            └── person.js
```

## Частые проблемы

### Порт 5555 занят

```bash
Get-Process python | Stop-Process -Force
```

### Агенты не подключаются

Проверь, что сервер запущен и открыт `http://127.0.0.1:5555`.

### Панель пустая

Открой DevTools (`F12`) → **Console**, смотри ошибки.

### holehe не работает

Нужен установленный `.exe`. Проверь:

```bash
python -c "import holehe; print(holehe.__file__)"
```

## Дисклеймер

⚠️ Инструмент предназначен для работы с открытыми источниками и **собственными данными**.

Использование для сбора информации о третьих лицах без их согласия может нарушать законодательство РФ (ст. 137 УК РФ, 152-ФЗ «О персональных данных») и аналогичные законы других стран.

Автор не несёт ответственности за неправомерное использование данного инструмента.

**Соблюдай этику и закон.** OSINT — это про открытые данные, а не про слежку и «пробив».

### Разрешено

- Проверка собственных данных (email, домен, ник, IP, телефон).
- Проверка данных с письменного согласия владельца.
- Проверка публичных персон по открытым источникам (в учебных целях).

### Запрещено

- Сбор информации о третьих лицах без их согласия.
- Использование закрытых/серых баз данных.
- Доксинг, сталкинг, шантаж, слежка.

## Лицензия

MIT License. Подробности — в файле [LICENSE](LICENSE).

## Автор

**REP_DOTA 2** — проект разрабатывается в учебных целях с 2026 года.