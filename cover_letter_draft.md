# Cover Letter Draft - Datapult Senior Data Engineer

**To**: Datapult Hiring Team
**From**: Danylo Kliuiev
**Re**: Senior Data Engineer Position

---

## Introduction

I've built a working proof-of-concept that demonstrates my ability to work with French open data:

**[Live Demo: https://frealestate.kliuiev.com/docs](https://frealestate.kliuiev.com/docs)**

This POC ingests real DVF (Demandes de Valeurs Foncières) data from data.gouv.fr, filters for large commercial/industrial properties (>=10,000 m²), and exposes them via a paginated REST API with Swagger documentation. The entire pipeline - from raw government CSV to production API - took less than a day to build.

---

## Relevant Experience

### Chernobyl NPP Document Management System (DDPRO LLC, 2016-2018)

Architected and built a document management system for the New Safe Confinement project:

- System operates **150,000+ files** and **20,000+ documents**
- Designed PostgreSQL database architecture from scratch
- Built data extraction pipelines using Selenium web scraping
- Implemented OCR processing for scanned technical drawings using Tesseract
- Deployed and maintained Linux servers on-site at client facility
- Created staff training materials and documentation

### Sports Analytics Platforms (StatRoute & Boost, 2018-2021)

Developed data pipelines and APIs for NFL/NBA analytics:

- **StatRoute**: REST API development, NFL/NBA analytics with Pandas, player comparison models, data validation with Pydantic
- **Boost**: PostgreSQL design and optimization, third-party API integrations (Sportradar, Arria NLG), basketball data parsing with Selenium

Both projects involved high-volume data ingestion, transformation, and real-time API delivery.

---

## Technical Match

| Requirement | My Experience |
|-------------|---------------|
| Python | 8+ years - Django, FastAPI, Pandas, Pydantic |
| PostgreSQL | Schema design, optimization, complex queries |
| Data Engineering | ETL pipelines, data validation, OCR processing |
| API Development | REST/GraphQL APIs, Swagger/OpenAPI, pagination |
| Cloud Infrastructure | AWS (SQS, SES, EKS), Azure, CKAD certified |
| Autonomous Work | Remote-first since 2019, self-directed delivery |

---

## Understanding of French Data Landscape

Through building this POC, I've gained practical experience with French open data sources:

**DVF (Demandes de Valeurs Foncières)**
- Transaction data including prices, surfaces, property types, and locations
- Publicly available via data.gouv.fr (no authorization required)
- Updated annually with geocoded versions available
- Data quality varies: some records have missing prices or nominal values (1 EUR for corporate transfers)

**Fichiers Fonciers**
- More comprehensive property data including ownership information, detailed parcel data, and building characteristics
- Requires authorized access through CEREMA
- Better suited for detailed property analysis beyond simple transactions

The POC demonstrates my ability to quickly understand French government data sources, handle their specific formats (CSV with French conventions), and work around data quality challenges.

---

## Availability

- **Immediate availability** for project start
- **Location**: Benidorm, Spain (CET timezone)
- **Work style**: Remote-first, responsive communication
- **Estimated ramp-up**: 1-2 weeks to full productivity on your codebase

---

## Next Steps

I'd welcome the opportunity to discuss:

1. The specific data sources and pipelines you're building
2. Your current architecture and where I can add the most value
3. Timeline, scope, and collaboration expectations

The POC is live and the code is available for review. Happy to walk through the implementation or extend it based on your feedback.

**Danylo Kliuiev**
- Email: danylo@kliuiev.com
- Portfolio: https://kliuiev.com
- POC Demo: https://frealestate.kliuiev.com/docs
- LinkedIn: /in/danylo-kliuiev/
- GitHub: /Rolloniel
