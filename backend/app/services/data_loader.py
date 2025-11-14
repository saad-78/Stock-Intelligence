from datetime import datetime, date
import pandas as pd
import yfinance as yf


from datetime import  timedelta
from typing import List


from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.stock import StockPrice

def to_python_date(value) -> date:
    if isinstance(value, pd.Series):
        if value.empty:
            raise ValueError("Empty Series for date value")
        value = value.iloc[0]
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime().date()
    if isinstance(value, str):
        return datetime.fromisoformat(value).date()
    raise ValueError(f"Unsupported date type: {type(value)}")



NSE_SUFFIX = ".NS"


def build_symbol(raw_symbol: str) -> str:
    if raw_symbol.endswith(NSE_SUFFIX):
        return raw_symbol
    return raw_symbol + NSE_SUFFIX


def fetch_stock_history(symbol: str, days: int = 365) -> pd.DataFrame:
    df = yf.download(
        symbol,
        period="1y",
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=True,
    )
    if df.empty:
        return df
    df.reset_index(inplace=True)
    return df



def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["DailyReturn"] = (df["Close"] - df["Open"]) / df["Open"]
    df["MA7"] = df["Close"].rolling(window=7, min_periods=1).mean()

    rolling_52w = df["Close"].rolling(window=252, min_periods=1)
    df["High52W"] = rolling_52w.max()
    df["Low52W"] = rolling_52w.min()

    df["Volatility30D"] = df["DailyReturn"].rolling(window=30, min_periods=1).std()

    df = df.ffill().bfill()
    df["Date"] = df["Date"].apply(to_python_date)
    return df




def ensure_company(db: Session, symbol: str, name: str = "", exchange: str = "NSE") -> Company:
    company = db.query(Company).filter(Company.symbol == symbol).first()
    if company:
        return company
    company = Company(symbol=symbol, name=name or symbol.replace(NSE_SUFFIX, ""), exchange=exchange)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def store_history(db: Session, symbol: str, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        date_value = to_python_date(row["Date"])

        existing = (
            db.query(StockPrice)
            .filter(StockPrice.symbol == symbol, StockPrice.date == date_value)
            .first()
        )
        if existing:
            continue

        record = StockPrice(
            symbol=symbol,
            date=date_value,
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
            adjusted_close=float(row.get("Adj Close", row["Close"])),
            volume=float(row.get("Volume", 0)),
            daily_return=float(row["DailyReturn"]),
            ma_7=float(row["MA7"]),
            high_52w=float(row["High52W"]),
            low_52w=float(row["Low52W"]),
            volatility_30d=float(row["Volatility30D"]),
        )
        db.add(record)
    db.commit()




def load_symbols(db: Session, symbols: List[str]) -> None:
    for raw_symbol in symbols:
        yf_symbol = build_symbol(raw_symbol)
        df = fetch_stock_history(yf_symbol)
        if df.empty:
            continue
        df = compute_metrics(df)
        ensure_company(db, yf_symbol)
        store_history(db, yf_symbol, df)
