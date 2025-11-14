from datetime import date

from pydantic import BaseModel


class StockPriceBase(BaseModel):
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float | None = None
    volume: float | None = None
    daily_return: float | None = None
    ma_7: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    volatility_30d: float | None = None


class StockPrice(StockPriceBase):
    id: int

    class Config:
        orm_mode = True


class StockSummary(BaseModel):
    symbol: str
    high_52w: float
    low_52w: float
    avg_close: float


class StockCompareMetrics(BaseModel):
    symbol: str
    return_30d: float
    avg_volatility_30d: float


class StockCompareResponse(BaseModel):
    symbol1: StockCompareMetrics
    symbol2: StockCompareMetrics
