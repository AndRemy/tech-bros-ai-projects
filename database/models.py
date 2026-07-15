from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Property(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(unique=True, index=True)
    title: str
    price_usd: float
    price_pen: Optional[float] = None
    bedrooms: int
    bathrooms: int
    area_m2: float
    price_m2_usd: float
    district: str = Field(index=True)
    # Ubicación precisa
    address: str = Field(index=True)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DistrictStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    district: str = Field(unique=True, index=True)
    avg_price_m2_usd: float
    total_properties_sampled: int
    updated_at: datetime = Field(default_factory=datetime.utcnow)
