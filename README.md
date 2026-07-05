# Airport Operations Predictive Analytics

> An end-to-end, automated AI system for predicting flight delay risk and forecasting passenger traffic — built with real US DOT/BTS data, deployed across three production services, and running autonomously without human intervention.

**Inspired by operational challenges observed during an internship at Lucknow International Airport (Adani Group).**

---

## Live Demo

| Service | URL | Status |
|---|---|---|
| Dashboard | https://airport-operations-predictive-analytics-pydn9pjwv-kartikeya5.vercel.app | Live |
| REST API | https://airport-backend-wc22.onrender.com/api/health | Live |
| ML Service | https://airport-operations-predictive-analytics.onrender.com/docs | Live |

---

## What Makes This "Automated AI-Driven"

Most ML projects require a human to trigger predictions. This system does not:

- **Every 6 hours** — the scheduler automatically generates delay risk predictions and stores them in PostgreSQL
- **Every day at 06:00** — a 30-day passenger traffic forecast runs automatically
- **On threshold breach** — when delay probability exceeds 65%, an alert fires automatically (logged to Render dashboard, email-configurable)
- **On startup** — if the database is empty, the DataSeeder populates 30 historical predictions automatically so the dashboard is never blank

---

## Architecture

```
React Dashboard (Vercel)
        |
        | HTTP
        v
Java Spring Boot Backend (Render) ←── PostgreSQL DB (Render)
        |                                    |
        | HTTP                               | stores predictions
        v                                    |
Python FastAPI ML Service (Render) ──────────┘
        |
        ├── XGBoost Delay Model (ROC-AUC: 0.8296)
        └── Prophet Traffic Forecast (MAPE: 3.18%)
```

---

## ML Models

### Delay Risk Prediction (XGBoost)
- **Data:** Real US DOT/BTS flight delay data (2013-2023), 171,223 records, 395 airports, 21 carriers
- **Target:** Binary classification — will a carrier-airport-month combination have >20% delayed flights?
- **ROC-AUC:** 0.8296 (no data leakage — future-looking aggregations explicitly excluded)
- **Features:** month, year, arr_flights, is_summer, is_winter_holiday, years_since_2013, airport_avg_delay_rate, carrier_avg_delay_rate

### Passenger Traffic Forecasting (Prophet)
- **Data:** 6 years of daily airport footfall (extended to current date)
- **MAPE:** 3.18% on 90-day holdout
- **MAE:** ~1,156 passengers/day
- **Output:** 30-day daily forecast with 95% confidence intervals

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Models | Python, XGBoost, Prophet, scikit-learn, SHAP |
| ML Service | FastAPI, Pydantic, Uvicorn, Docker |
| Backend | Java 17, Spring Boot 4.1, Spring Data JPA, Spring Mail |
| Database | PostgreSQL (production), H2 (local dev) |
| Automation | Spring `@Scheduled` — daily forecasts, risk scans, continuous monitoring |
| Dashboard | React 18, Vite, Recharts, Axios |
| Deployment | Render (ML service + backend + DB), Vercel (dashboard) |
| Testing | pytest (15 tests, 100% pass), JUnit |
| DevOps | Docker multi-stage builds, GitHub Actions CI/CD |

---

## Project Structure

```
airport-operations-predictive-analytics/
├── ml-service/              # Python FastAPI ML microservice
│   ├── app/
│   │   ├── main.py          # FastAPI endpoints
│   │   ├── services.py      # ML inference layer
│   │   └── config.py        # Environment-based configuration
│   ├── ml/
│   │   ├── train_delay.py   # XGBoost training pipeline
│   │   └── train_traffic.py # Prophet training pipeline
│   ├── tests/               # 15 pytest tests (100% passing)
│   └── Dockerfile           # Multi-stage production build
│
├── backend/                 # Java Spring Boot backend
│   └── src/main/java/com/kartikeya/airportbackend/
│       ├── controller/      # REST endpoints
│       ├── service/         # Business logic + ML client
│       ├── scheduler/       # Automated daily jobs
│       ├── seeder/          # Database pre-population
│       ├── alert/           # Email alert system
│       ├── entity/          # JPA entities (PostgreSQL)
│       └── exception/       # Global error handling
│
├── frontend/                # React dashboard
│   └── src/
│       ├── App.jsx          # Main dashboard
│       ├── ForecastChart.jsx # 30-day Prophet forecast chart
│       ├── PredictionForm.jsx # Real model input form
│       ├── AlertPanel.jsx   # Auto-refreshing alerts
│       └── useAutoRefresh.js # 5-minute auto-refresh hook
│
└── docker-compose.yml       # Local full-stack development
```

---

## Running Locally

### Prerequisites
- Python 3.11, Java 17, Node.js 22, Docker Desktop

### ML Service
```bash
cd ml-service
python -m venv venv && venv/Scripts/activate   # Windows
pip install -r requirements.txt
python ml/train_delay.py
python ml/train_traffic.py
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

### Backend
```bash
cd backend
# Set ML_SERVICE_URL=http://localhost:8000 in application.properties
./mvnw spring-boot:run
# API: http://localhost:8080/api/health
```

### Dashboard
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8080" > .env
npm run dev
# Dashboard: http://localhost:5173
```

### Full stack with Docker
```bash
docker compose up --build
```

---

## Data

Raw data files are gitignored (too large for version control). To reproduce:

```bash
# Install Kaggle CLI
pip install kaggle

# Download real US DOT/BTS data
kaggle datasets download -d sriharshaeedala/airline-delay -p ml-service/data --unzip

# Clean and engineer features
python ml-service/scripts/clean_and_engineer.py

# Retrain models
python ml-service/ml/train_delay.py
python ml-service/ml/train_traffic.py
```

---

## API Reference

### ML Service (FastAPI) — port 8000

| Endpoint | Method | Description |
|---|---|---|
| `/predict` | POST | XGBoost delay risk prediction |
| `/forecast/traffic` | GET | Prophet 1-365 day forecast |
| `/health` | GET | Model health + metadata |
| `/docs` | GET | Interactive Swagger UI |

### Backend (Spring Boot) — port 8080

| Endpoint | Method | Description |
|---|---|---|
| `/api/predict/delay` | POST | Predict + persist to DB |
| `/api/forecast/traffic` | GET | Traffic forecast |
| `/api/dashboard/summary` | GET | Aggregated stats |
| `/api/history` | GET | Last 20 predictions |
| `/api/history/alerts` | GET | High-risk predictions only |
| `/api/health` | GET | Backend + ML service health |

---

## Automated Jobs

| Job | Schedule | Action |
|---|---|---|
| Daily Forecast | 06:00 daily | Fetches 30-day forecast, alerts if any day > 45,000 passengers |
| Risk Scan | 06:05 daily | Scans last 24h predictions, alerts if high-risk count > 0 |
| Continuous Monitor | Every 6 hours | Generates prediction for current month, alerts if probability > 65% |
| Data Seeder | On startup | Populates DB with historical predictions if empty |

---

## Key Design Decisions

**Why XGBoost over deep learning?**
XGBoost is interpretable (SHAP explainability), faster to train, and performs comparably to LSTMs on tabular data. Interpretability matters in operations contexts where staff need to understand *why* a delay is predicted, not just *that* it is.

**Why Python + Java rather than one language?**
Real enterprise airport systems use Java for backend orchestration (Spring Boot is the industry standard for enterprise APIs) and Python for ML (the ecosystem has no peer). Building both demonstrates the architecture pattern used in production at companies like Adani, Infosys, and TCS.

**Why aggregate-level rather than per-flight prediction?**
The real US DOT dataset is aggregate (carrier + airport + month). This is actually more operationally useful — airport ops teams plan at the route/carrier level, not per individual flight.

---

## Author

**Kartikeya Maulekhi**
B.Tech Computer Science (AI/ML), DIT University, Dehradun
Internship: IT Infrastructure, Lucknow International Airport (Adani Group)

[![GitHub](https://img.shields.io/badge/GitHub-kartikeyamaulekhi-black)](https://github.com/kartikeyamaulekhi)
