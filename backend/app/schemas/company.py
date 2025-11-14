from pydantic import BaseModel


class CompanyBase(BaseModel):
    symbol: str
    name: str
    exchange: str


class Company(CompanyBase):
    id: int

    class Config:
        orm_mode = True
