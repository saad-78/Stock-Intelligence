from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    adjusted_close = Column(Float, nullable=True)
    volume = Column(Float, nullable=True)
    daily_return = Column(Float, nullable=True)
    ma_7 = Column(Float, nullable=True)
    high_52w = Column(Float, nullable=True)
    low_52w = Column(Float, nullable=True)
    volatility_30d = Column(Float, nullable=True)

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    company = relationship("Company", backref="prices")
