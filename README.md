## FindFirst

Emergency coordination app for missing-person reports, volunteer tracking, weather-aware risk scoring, and team assignment.

## Quick Start

1. Open the project folder:

```bash
cd /Users/ivanzabila/Downloads/hackatoned
```

2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

3. Run the app:

```bash
streamlit run app.py
```

4. Open the local URL:

```text
http://localhost:8501
```

The app also starts a local FastAPI heartbeat server on `http://localhost:8000`.

## Demo Accounts

| Role | Username | Password |
| --- | --- | --- |
| Volunteer | `ivan` | `1234` |
| Volunteer | `sarah` | `1234` |
| Volunteer | `mike` | `1234` |
| Admin / Volunteer | `admin` | `admin` |
| Reporter | `julia` | `1234` |
| Reporter | `alex` | `1234` |

## Browser Geolocation

Volunteer check-ins require browser geolocation. Open the app on `localhost` or HTTPS, then click `Request Location Access` in `Tracking & Check-ins`.

If the native browser permission popup does not appear:

- Check that the URL is `http://localhost:8501` locally, or HTTPS in deployment.
- Click the site settings icon in the browser address bar.
- Set `Location` to `Allow`.
- Reload the app and click `Request Location Access` again.

## Heartbeat Agent

Optional examples for sending volunteer heartbeat pings from a separate process:

```bash
python3 agent.py --id V002 --server http://localhost:8000 --interval 30
python3 agent.py --id V003 --server http://localhost:8000 --interval 30
python3 agent.py --id V004 --server http://localhost:8000 --interval 30
```

Useful endpoint:

```text
POST /offline/{vol_id}
```

## Troubleshooting

- If the app does not open, check that Streamlit printed `Local URL: http://localhost:8501`.
- If port `8501` is busy, run:

```bash
streamlit run app.py --server.port 8502
```

- If the heartbeat API port `8000` is busy, the app will try the next free port. Check the UI line `Heartbeat server running on :PORT`.
- If dependencies are missing, run:

```bash
python3 -m pip install -r requirements.txt
```
