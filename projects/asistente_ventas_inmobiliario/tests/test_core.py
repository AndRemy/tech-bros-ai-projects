import pytest
from sqlmodel import Session, select
from database.db import engine, init_db
from database.models import DistrictStats, Property
from utils.helpers import calculate_price_m2, compare_to_average, format_currency
from ingestion.ingestor import ingest_property_link

def test_helpers():
    """Test standard math and formatting helper calculations."""
    # Test calculate_price_m2
    assert calculate_price_m2(150000.0, 75.0) == 2000.0
    assert calculate_price_m2(150000.0, 0.0) == 0.0
    
    # Test format_currency
    assert format_currency(12345.67, "USD") == "$12,345.67"
    assert format_currency(12345.67, "PEN") == "S/. 12,345.67"
    
    # Test compare_to_average
    comp_under = compare_to_average(1800.0, 2000.0)
    assert comp_under["deviation_pct"] == -10.0
    assert "Subvalorado" in comp_under["evaluation"]
    
    comp_over = compare_to_average(2300.0, 2000.0)
    assert comp_over["deviation_pct"] == 15.0
    assert "Sobrevalorado" in comp_over["evaluation"]

def test_database_init():
    """Test that the database initializes correctly with default seeds."""
    # Run database initialization
    init_db()
    
    # Verify that seed stats were created in the SQLite database
    with Session(engine) as session:
        stats = session.exec(select(DistrictStats)).all()
        assert len(stats) >= 8
        
        miraflores = session.exec(select(DistrictStats).where(DistrictStats.district == "Miraflores")).first()
        assert miraflores is not None
        assert miraflores.avg_price_m2_usd == 2000.0

def test_analyze_link_fallback():
    """Test property analyzer tool with simulated fallback execution."""
    # This uses a dummy link, should resolve to a safe mock result but save it to DB
    url = "https://urbania.pe/inmueble/departamento-en-miraflores-1234"
    
    # Use ingestor instead of the agent tool
    success = ingest_property_link(url)
    assert success == True
    
    # Check that it saved the property to the SQLite DB
    with Session(engine) as session:
        prop = session.exec(select(Property).where(Property.url == url)).first()
        assert prop is not None
        assert prop.district == "Miraflores"
        assert prop.price_usd == 185000.0
        assert prop.area_m2 == 85.0
