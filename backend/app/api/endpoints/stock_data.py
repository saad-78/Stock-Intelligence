from datetime import datetime, timedelta
from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.stock import StockPrice
from app.schemas.stock import StockPrice as StockPriceSchema
from app.schemas.stock import StockSummary, StockCompareMetrics, StockCompareResponse


router = APIRouter(tags=["stocks"])

NSE_SUFFIX = ".NS"

SUMMARY_TTL_SECONDS = 300
SUMMARY_CACHE: dict[str, dict[str, Any]] = {}


def normalize_symbol(raw_symbol: str) -> str:
  if raw_symbol.endswith(NSE_SUFFIX):
    return raw_symbol
  return raw_symbol + NSE_SUFFIX


@router.get("/data/{symbol}", response_model=List[StockPriceSchema])
async def get_last_30_days(symbol: str, db: Session = Depends(get_db)):
  norm_symbol = normalize_symbol(symbol.upper())
  rows = (
    db.query(StockPrice)
    .filter(StockPrice.symbol == norm_symbol)
    .order_by(StockPrice.date.desc())
    .limit(30)
    .all()
  )
  if not rows:
    raise HTTPException(status_code=404, detail="Symbol not found")
  rows.reverse()
  return rows


@router.get("/summary/{symbol}", response_model=StockSummary)
async def get_summary(symbol: str, db: Session = Depends(get_db)):
  norm_symbol = normalize_symbol(symbol.upper())
  now = datetime.utcnow()
  cached = SUMMARY_CACHE.get(norm_symbol)
  if cached and cached["expires_at"] > now:
    return cached["value"]

  exists = db.query(StockPrice.id).filter(StockPrice.symbol == norm_symbol).first()
  if not exists:
    raise HTTPException(status_code=404, detail="Symbol not found")

  agg = (
    db.query(
      func.max(StockPrice.high_52w),
      func.min(StockPrice.low_52w),
      func.avg(StockPrice.close),
    )
    .filter(StockPrice.symbol == norm_symbol)
    .one()
  )

  high_52w, low_52w, avg_close = agg

  if high_52w is None or low_52w is None or avg_close is None:
    raise HTTPException(status_code=400, detail="Insufficient data for summary")

  result = StockSummary(
    symbol=norm_symbol,
    high_52w=float(high_52w),
    low_52w=float(low_52w),
    avg_close=float(avg_close),
  )

  SUMMARY_CACHE[norm_symbol] = {
    "value": result,
    "expires_at": now + timedelta(seconds=SUMMARY_TTL_SECONDS),
  }

  return result


def compute_30d_metrics(db: Session, norm_symbol: str) -> StockCompareMetrics:
  rows = (
    db.query(StockPrice)
    .filter(StockPrice.symbol == norm_symbol)
    .order_by(StockPrice.date.desc())
    .limit(30)
    .all()
  )
  if len(rows) < 2:
    raise HTTPException(status_code=400, detail=f"Insufficient data for {norm_symbol}")
  rows.reverse()
  start = rows[0]
  end = rows[-1]
  if start.close == 0:
    raise HTTPException(status_code=400, detail=f"Invalid price data for {norm_symbol}")

  return_30d = (end.close - start.close) / start.close

  vols = [r.volatility_30d for r in rows if r.volatility_30d is not None]
  if not vols:
    avg_volatility = 0.0
  else:
    avg_volatility = float(sum(vols) / len(vols))

  return StockCompareMetrics(
    symbol=norm_symbol,
    return_30d=float(return_30d),
    avg_volatility_30d=avg_volatility,
  )


@router.get("/compare", response_model=StockCompareResponse)
async def compare_stocks(
  symbol1: str = Query(...),
  symbol2: str = Query(...),
  db: Session = Depends(get_db),
):
  norm_symbol1 = normalize_symbol(symbol1.upper())
  norm_symbol2 = normalize_symbol(symbol2.upper())

  metrics1 = compute_30d_metrics(db, norm_symbol1)
  metrics2 = compute_30d_metrics(db, norm_symbol2)

  return StockCompareResponse(symbol1=metrics1, symbol2=metrics2)
