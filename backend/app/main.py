from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine, SessionLocal
from app.services.data_loader import load_symbols
from app.api.endpoints import companies, stock_data


app = FastAPI(
    title="Stock Data Intelligence API",
    version="0.1.0",
)

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://stock-intelligence.vercel.app",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]
        load_symbols(db, symbols)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(companies.router)
app.include_router(stock_data.router)
