# Telegram Task Bot

Простой Telegram-бот для командной работы с общим списком задач.

## Возможности

- `/start` — приветствие и список команд
- `/add <текст задачи>` — добавить задачу в общий список
- `/list` — показать все задачи
- `/list_csv` — получить задачи в CSV-файле

## Структура проекта

```text
telegram_task_bot/
├── main.py              # Точка входа
├── config.py            # Настройки (токен, путь к БД)
├── requirements.txt     # Зависимости
├── db/
│   ├── __init__.py
│   └── database.py      # Работа с SQLite3
├── handlers/
│   ├── __init__.py
│   ├── start.py         # Обработчик /start
│   └── tasks.py         # Обработчики /add, /list, /list_csv
└── keyboards/
    ├── __init__.py
    └── common.py        # Клавиатуры бота
```

## Установка и запуск

1. Перейдите в папку проекта:

   ```bash
   cd telegram_task_bot
   ```

2. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

3. Задайте токен бота, полученный у [@BotFather](https://t.me/BotFather).

   Создайте файл `.env` на основе `.env.example` и укажите токен:

   ```env
   BOT_TOKEN=ВАШ_ТОКЕН
   ```

   Или задайте переменную окружения:

   **PowerShell:**

   ```powershell
   $env:BOT_TOKEN="ВАШ_ТОКЕН"
   ```

   **CMD:**

   ```cmd
   set BOT_TOKEN=ВАШ_ТОКЕН
   ```

   **Linux/macOS:**

   ```bash
   export BOT_TOKEN="ВАШ_ТОКЕН"
   ```

4. Запустите бота:

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
