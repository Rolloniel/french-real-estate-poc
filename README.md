# French Warehouse Real Estate Explorer

Interactive map and analytics dashboard for large warehouse transactions in France, powered by government open data (DVF).

![Screenshot](screenshot.png)

## Features

- **Interactive Map** -- Browse warehouse transactions as map pins with Leaflet, click for details
- **Filter Panel** -- Narrow results by department, price range, surface area, date range, and commune
- **Proximity Search** -- Find warehouses within a configurable radius of any point on the map
- **Choropleth Heatmap** -- Department-level shading by average price per m2
- **Analytics Dashboard** -- Price distribution histograms, department comparisons, price trends over time, top/bottom communes
- **DVF Ingestion Pipeline** -- Automated download and filtering of French government real estate transaction data

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js | 16.x |
| UI | React | 19.x |
| Styling | Tailwind CSS | 4.x |
| Maps | Leaflet + react-leaflet | 1.9 / 5.x |
| Charts | Recharts | 3.x |
| Backend | FastAPI | 0.109+ |
| Runtime | Python | 3.12 |
| Database | Supabase (PostgreSQL) | -- |
| Containerization | Docker Compose | -- |

## Architecture

```
Frontend (Next.js)  -->  /api/* rewrite  -->  Backend (FastAPI)  -->  Supabase PostgreSQL
                                                                          ^
                                                                          |
                                              Ingestion Script (Python) --+
                                              Downloads DVF CSVs from data.gouv.fr,
                                              filters for warehouses >= 10,000 m2,
                                              inserts via service role key
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- A Supabase project with a `warehouses` table (see schema below)

### 1. Clone

```bash
git clone <repo-url>
cd <repo-dir>
```

### 2. Environment variables

```bash
cp .env.example .env
# Fill in your Supabase credentials
```

### 3. Start the stack

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health check: http://localhost:8000/health

### 4. Ingest data

Run the ingestion script from the project root (requires a Python environment with dependencies installed):

```bash
pip install -r requirements.txt
python -m scripts.ingest_dvf --departments 77
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/warehouses` | List warehouses (paginated, filterable by department, price, surface, date, commune) |
| `GET` | `/api/warehouses/nearby` | Find warehouses within a radius of a lat/lng point |
| `GET` | `/api/departments` | List unique department codes for filter dropdowns |
| `GET` | `/api/stats` | Summary stats: count, average price, total surface |
| `GET` | `/api/analytics/price-per-m2` | Price per m2 histogram with mean and median |
| `GET` | `/api/analytics/by-department` | Average price, surface, and price/m2 grouped by department |
| `GET` | `/api/analytics/price-trends` | Monthly average price and price/m2 over time |
| `GET` | `/api/analytics/top-communes` | Top 10 most expensive and cheapest communes by price/m2 |
| `GET` | `/api/analytics/department-stats` | Per-department avg price/m2 and count (for choropleth) |

## Data Source

This project uses **DVF (Donnees de Valeur Fonciere)** -- French government open data on real estate transactions published by the Direction Generale des Finances Publiques.

- Source: https://files.data.gouv.fr/geo-dvf/latest/csv/
- Coverage: All French departments (mainland + overseas), 2024 data
- The ingestion pipeline downloads per-department gzipped CSVs, filters for industrial/commercial properties ("Local industriel, commercial ou assimile") with surface area >= 10,000 m2 and a recorded price, then inserts the results into Supabase

### Warehouses table schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key (auto-generated) |
| `dvf_mutation_id` | text | DVF transaction identifier |
| `address` | text | Street address |
| `postal_code` | text | Postal code |
| `commune` | text | Municipality name |
| `department` | text | Department code |
| `surface_m2` | float | Building surface in m2 |
| `price_eur` | float | Transaction price in EUR |
| `transaction_date` | date | Date of transaction |
| `latitude` | float | GPS latitude |
| `longitude` | float | GPS longitude |
| `property_type` | text | DVF property type string |

## Ingestion Script

```bash
# Ingest a single department (default: 77)
python -m scripts.ingest_dvf

# Ingest specific departments
python -m scripts.ingest_dvf --departments 75,77,78,92,93,94

# Ingest all French departments (mainland + overseas)
python -m scripts.ingest_dvf --all

# Limit records per department (useful for testing)
python -m scripts.ingest_dvf --departments 77 --limit 10
```

Flags `--all` and `--departments` are mutually exclusive. When neither is provided, only department 77 (Seine-et-Marne) is processed.

## Development (without Docker)

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/api/*` requests to the backend via Next.js rewrites. Set `BACKEND_URL` to override the backend address (defaults to `http://localhost:8000`).

## License

Private project -- not licensed for redistribution.
