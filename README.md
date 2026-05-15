## Запуск сайту
## Быстрый запуск


1. Перейти в папку проекта:

```bash
cd /Users/ivanzabila/Downloads/hackatoned
```

2. Установить зависимости:

```bash
python3 -m pip install -r requirements.txt
```

3. Запустить сайт:

```bash
streamlit run app.py

Відкрити сайт: http://localhost:8501
4. Открыть в браузере:

```text
http://localhost:8501
```

Если нужно запустить именно открытый в IDE файл:

```bash
streamlit run "app (2).py"
```

Но основной вариант для запуска:

```bash
streamlit run app.py
```

Під час запуску `app.py` також піднімає локальний FastAPI heartbeat-сервер на http://localhost:8000.

## Demo accounts
## Demo accounts / логины


- Volunteers: `ivan`, `sarah`, `mike`, `admin`
- Reporters: `julia`, `alex`
| Role | Username | Password |
| --- | --- | --- |
| Volunteer | `ivan` | `1234` |
| Volunteer | `sarah` | `1234` |
| Volunteer | `mike` | `1234` |
| Reporter | `julia` | `1234` |
| Reporter | `alex` | `1234` |
| Admin / Volunteer | `admin` | `admin` |


## Heartbeat agent
## Heartbeat agent / online + GPS


Примеры для других demo-волонтеров:

```bash
python3 agent.py --id V002 --server http://localhost:8000 --interval 30
python3 agent.py --id V003 --server http://localhost:8000 --interval 30
python3 agent.py --id V004 --server http://localhost:8000 --interval 30
```

Корисні API:
- `POST /offline/{vol_id}`

## Если что-то не запускается

- Если сайт не открывается, проверь, что Streamlit пишет `Local URL: http://localhost:8501`.
- Если порт `8501` занят:

```bash
streamlit run app.py --server.port 8502
```

- Если heartbeat API на `8000` занят другим процессом, приложение попробует найти следующий свободный порт. Тогда в UI смотри строку `Heartbeat server running on :PORT`.
- Если зависимости не установились, повтори:

```bash
python3 -m pip install -r requirements.txt
```