# Telegram Task Bot

Простой Telegram-бот для командной работы с общим списком задач. Задачи хранятся в SQLite-базе `tasks.db`.

## Возможности

- `/start` — приветствие и список команд
- `/add <текст задачи>` — добавить задачу в общий список
- `/add` — добавить задачу пошагово: бот спросит текст следующим сообщением
- `/cancel` — отменить пошаговый ввод задачи
- `/list` — показать все задачи (при большом количестве список будет разбит на несколько сообщений)
- `/list_csv` — получить задачи в CSV-файле

## Структура проекта

```text
telegram_task_bot/
├── main.py              # Точка входа
├── config.py            # Настройки (токен, прокси, путь к БД)
├── requirements.txt     # Зависимости
├── .env.example         # Пример файла с настройками
├── db/
│   ├── __init__.py
│   └── database.py      # Работа с SQLite3
├── handlers/
│   ├── __init__.py
│   ├── start.py         # Обработчик /start
│   └── tasks.py         # Обработчики /add, /cancel, /list, /list_csv
└── keyboards/
    ├── __init__.py
    └── common.py        # Клавиатура бота
```

## Установка и запуск

1. Перейдите в папку проекта:

   ```bash
   cd telegram_task_bot
   ```

2. Создайте и активируйте виртуальное окружение:

   **Windows (PowerShell):**

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **Linux/macOS:**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Задайте токен бота, полученный у [@BotFather](https://t.me/BotFather).

   Создайте файл `.env` на основе `.env.example`:

   ```env
   BOT_TOKEN=ВАШ_ТОКЕН
   ```

   Если для доступа к Telegram API нужен прокси, добавьте в `.env`:

   ```env
   PROXY_URL=socks5://127.0.0.1:10808
   ```

   Без `PROXY_URL` бот подключается к Telegram напрямую. Вместо файла `.env` можно использовать переменные окружения:

   **PowerShell:**

   ```powershell
   $env:BOT_TOKEN="ВАШ_ТОКЕН"
   $env:PROXY_URL="socks5://127.0.0.1:10808"
   ```

   **CMD:**

   ```cmd
   set BOT_TOKEN=ВАШ_ТОКЕН
   set PROXY_URL=socks5://127.0.0.1:10808
   ```

   **Linux/macOS:**

   ```bash
   export BOT_TOKEN="ВАШ_ТОКЕН"
   export PROXY_URL="socks5://127.0.0.1:10808"
   ```

5. Запустите бота:

   ```bash
   python main.py
   ```

## База данных

Бот использует SQLite3. Файл базы данных `tasks.db` создаётся автоматически в папке проекта при первом запуске.

Таблица `tasks`:

| Поле       | Тип     | Описание                     |
|------------|---------|------------------------------|
| id         | INTEGER | Уникальный ID задачи         |
| text       | TEXT    | Текст задачи                 |
| user       | TEXT    | Имя пользователя             |
| created_at | TEXT    | Дата и время создания        |

Файл `tasks.db` и файл `.env` с токеном добавлены в `.gitignore` и не должны попадать в репозиторий.
