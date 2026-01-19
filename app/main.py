from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import warehouses

app = FastAPI(
    title="French Real Estate POC API",
    description="POC demonstrating French open data (DVF) ingestion",
    version="0.1.0",
)

# CORS - allow all for POC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(warehouses.router)


@app.get("/health")
async def health():
    return {"status": "healthy"}
