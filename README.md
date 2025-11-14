# Stock Data Intelligence Dashboard

Mini financial data platform built for the Jarnox internship assignment.  
It collects real NSE stock data, computes analytics, exposes REST APIs with FastAPI, and shows an interactive dashboard with charts and a prediction line.

## 1. Tech Stack

- Backend: FastAPI, Python 3.12, SQLAlchemy, SQLite (configurable to PostgreSQL)
- Data: yfinance, pandas, numpy
- Frontend: HTML, CSS, vanilla JavaScript, Chart.js
- Extras: Simple ML (linear regression prediction), in-memory caching, Dockerfile for backend

## 2. Project Structure

stock-intelligence-platform/
├── backend/
│ ├── app/
│ │ ├── api/
│ │ │ ├── deps.py
│ │ │ └── endpoints/
│ │ │ ├── companies.py
│ │ │ └── stock_data.py
│ │ ├── core/
│ │ │ ├── config.py
│ │ │ └── database.py
│ │ ├── models/
│ │ │ ├── company.py
│ │ │ └── stock.py
│ │ ├── schemas/
│ │ │ ├── company.py
│ │ │ └── stock.py
│ │ └── services/
│ │ └── data_loader.py
│ ├── main.py
│ ├── requirements.txt
│ ├── Dockerfile
│ └── .env
├── frontend/
│ ├── index.html
│ ├── styles.css
│ └── app.js
└── docker-compose.yml


## 3. Setup (Local, Without Docker)

### 3.1 Backend

cd backend
python3 -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

pip install -r requirements.txt


Create `.env` in `backend`:

DATABASE_URL=sqlite:///./stock_data.db


Run API:

uvicorn app.main:app --reload

text

API docs:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

On startup, the app:

- Creates database tables  
- Downloads ~1 year of data for a few NSE symbols using yfinance  
- Computes metrics and stores them (see Part 1)

### 3.2 Frontend

In another terminal:

cd frontend
python3 -m http.server 5500

text

Open:

http://127.0.0.1:5500/index.html


The frontend expects the backend at `http://127.0.0.1:8000` (configurable in `app.js`).

## 4. Data & Metrics (Part 1)

- Data source: yfinance for NSE symbols (e.g. RELIANCE.NS, TCS.NS, INFY.NS).  
- Cleaning with pandas:
  - Date column parsed to proper dates.
  - Missing values handled with forward/backward fill.
- Stored in SQLite via SQLAlchemy models `Company` and `StockPrice`.

Computed metrics:

- Daily Return: `(Close - Open) / Open`
- 7-day Moving Average: rolling mean of Close
- 52-week High / 52-week Low: rolling 252-day max/min of Close
- Volatility score (custom metric): 30-day rolling standard deviation of daily returns

These fields are persisted in `stock_prices` and used by the APIs and UI.

## 5. API Design (Part 2)

All endpoints are implemented with FastAPI.

### 5.1 Endpoints

- `GET /companies`  
  - Returns list of companies (symbol, name, exchange).  
  - In-memory cache (5 minutes TTL) to avoid repeated DB hits.

- `GET /data/{symbol}`  
  - Returns last 30 days of stock data for the symbol.  
  - Fields include open, high, low, close, volume, daily_return, ma_7, high_52w, low_52w, volatility_30d.

- `GET /summary/{symbol}`  
  - Returns:
    - 52-week high  
    - 52-week low  
    - Average close  
  - Cached per symbol for 5 minutes.

- `GET /compare?symbol1=INFY&symbol2=TCS`  
  - Computes for each symbol:
    - 30-day return  
    - Average 30-day volatility  
  - Returns a structured JSON object suitable for charts.

Swagger UI documents all endpoints automatically.

## 6. Dashboard (Part 3)

The frontend dashboard provides:

- Left sidebar: list of companies loaded from `/companies`.
- Main price chart:
  - Close price time-series line.
  - 7-day moving average visible through the smoothed curve.
  - Prediction line: 7-day forward projection using simple linear regression over closing prices.
  - Range filters: Last 30 / 90 / 180 days (client-side slicing).

- Comparison chart:
  - Bar chart showing 30-day return vs average 30-day volatility for two selected stocks using `/compare`.

- Insights section:
  - Selected Summary: 52-week high, low, and average close from `/summary/{symbol}`.
  - Top Gainers (30d): top 5 stocks by 30-day return.
  - Top Losers (30d): bottom 5 by 30-day return.

## 7. Optional Add-ons (Part 4)

### 7.1 ML Prediction

- Uses simple linear regression on the last N closing prices on the frontend.  
- Predicts the next 7 days and overlays them as a dashed “Prediction” line on the main chart.

### 7.2 Async and Caching

- Async FastAPI endpoints for `/companies`, `/data/{symbol}`, `/summary/{symbol}`, and `/compare`.  
- In-memory TTL caching:
  - `/companies` list (5 minutes).
  - `/summary/{symbol}` per symbol (5 minutes).

### 7.3 Docker

Backend Dockerfile (`backend/Dockerfile`):

- Uses `python:3.12-slim`.  
- Installs dependencies from `requirements.txt`.  
- Copies `app/` and `.env`.  
- Runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

Build and run:

cd backend
docker build -t stock-intelligence-backend .
docker run --env-file .env -p 8000:8000 stock-intelligence-backend


Docker Compose (`docker-compose.yml`):

cd ..
docker-compose up --build


### 7.4 Deployment (to be filled once deployed)

- Backend: URL (Render / other).  
- Frontend: URL (GitHub Pages / other).  
- In `frontend/app.js`, `API_BASE` is updated to the deployed backend URL.

## 8. How This Meets the Assignment

- Part 1: Real NSE data, pandas cleaning, derived metrics, volatility score.  
- Part 2: Clean REST API with FastAPI and Swagger docs.  
- Part 3: Interactive dashboard with filters, comparison, and insights.  
- Part 4:
  - ML prediction line (linear regression).
  - Async endpoints + in-memory caching.
  - Dockerized backend and compose file for easy deployment.

## 9. Running Tests / Manual Checks

- Use `/health` endpoint to confirm backend is up.  
- Use `/companies`, `/data/{symbol}`, `/summary/{symbol}`, `/compare` via Swagger UI or curl.  
- Verify charts and insights update when switching companies and ranges.