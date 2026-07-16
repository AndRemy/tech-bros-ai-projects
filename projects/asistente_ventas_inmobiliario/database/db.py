import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session, select
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/real_estate.db")

# Fix SQLite multi-thread issues in dev if using sqlite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Ensure data directory exists
os.makedirs("./data", exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    SQLModel.metadata.create_all(engine)
    
    # Populate initial mock stats for Lima districts to enable instant demonstration
    from database.models import DistrictStats
    
    initial_stats = [
        DistrictStats(district="Miraflores", avg_price_m2_usd=2000.0, total_properties_sampled=150),
        DistrictStats(district="San Isidro", avg_price_m2_usd=2200.0, total_properties_sampled=120),
        DistrictStats(district="Barranco", avg_price_m2_usd=2100.0, total_properties_sampled=90),
        DistrictStats(district="Santiago de Surco", avg_price_m2_usd=1600.0, total_properties_sampled=250),
        DistrictStats(district="San Borja", avg_price_m2_usd=1700.0, total_properties_sampled=140),
        DistrictStats(district="Magdalena del Mar", avg_price_m2_usd=1500.0, total_properties_sampled=180),
        DistrictStats(district="Lince", avg_price_m2_usd=1400.0, total_properties_sampled=110),
        DistrictStats(district="Jesus Maria", avg_price_m2_usd=1450.0, total_properties_sampled=160),
    ]
    
    with Session(engine) as session:
        # Check if we already have stats
        existing_stats = session.exec(select(DistrictStats)).first()
        if not existing_stats:
            for stat in initial_stats:
                # Normalize district name to title case
                stat.district = stat.district.strip().title()
                session.add(stat)
            session.commit()
            print("Database initialized and default district statistics seeded!")
        else:
            print("Database already initialized.")
