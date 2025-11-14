from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.company import Company
from app.schemas.company import Company as CompanySchema


router = APIRouter(prefix="/companies", tags=["companies"])

CACHE_TTL_SECONDS = 300
COMPANIES_CACHE = {"data": None, "expires_at": None}


@router.get("", response_model=List[CompanySchema])
async def list_companies(db: Session = Depends(get_db)):
  now = datetime.utcnow()
  if (
    COMPANIES_CACHE["data"] is not None
    and COMPANIES_CACHE["expires_at"] is not None
    and COMPANIES_CACHE["expires_at"] > now
  ):
    return COMPANIES_CACHE["data"]

  companies = db.query(Company).order_by(Company.symbol).all()
  COMPANIES_CACHE["data"] = companies
  COMPANIES_CACHE["expires_at"] = now + timedelta(seconds=CACHE_TTL_SECONDS)
  return companies
