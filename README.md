недоделанный регер и накрутчик валюты дурак онлайн (но рабочий)

apple js reverse and gmail api by ироничныйчерт

dorabotki and apple kod analyzing by lvnlvn

## Установка и настройка

### Вариант 1: С использованием uv (рекомендуется)

1. **Установить uv:**
   ```bash
   # На macOS/Linux:
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # На Windows (PowerShell):
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Или через pip:
   pip install uv
   ```

2. **Установить зависимости:**
   ```bash
   uv sync
   ```

3. **Запустить проект:**
   ```bash
   uv run python main.py
   ```

### Вариант 2: Без uv (классический способ)

1. **Создать виртуальное окружение:**
   ```bash
   python -m venv venv
   
   # Активировать окружение:
   # На Linux/macOS:
   source venv/bin/activate
   # На Windows:
   venv\Scripts\activate
   ```

2. **Установить зависимости:**
   ```bash
   pip install requests loguru
   ```

3. **Запустить проект:**
   ```bash
   python main.py
   ```

## Настройка

1. **Отредактировать config.py:**
   - Настроить токены и ключи API
   - Указать прокси (при необходимости)
   - Настроить пути к файлам

2. **Подготовить cookies файлы:**
   - Поместить файлы .txt с cookies Gmail в папку `gmail_cookies/`
   - Имя файла должно содержать email адрес

## Запуск

```bash
# С uv:
uv run python main.py

# Без uv (в активированном venv):
python main.py
```
