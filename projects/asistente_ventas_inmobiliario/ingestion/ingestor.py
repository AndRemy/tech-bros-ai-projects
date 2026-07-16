import logging
from sqlmodel import Session, select
from database.db import engine
from database.models import Property, DistrictStats
from scrapper.urbania_scraper import scrape_property_url

logger = logging.getLogger(__name__)

def ingest_property_link(url: str) -> bool:
    """
    Scrapes a property link and saves it directly to the database.
    """
    import asyncio
    try:
        # Resolve async call
        property_data = asyncio.run(scrape_property_url(url))
    except Exception as e:
        logger.error(f"Error scraping property {url}: {e}")
        return False
    
    if not property_data.get("success", False):
        logger.error(f"Failed to scrape property {url}")
        return False
    
    district = property_data["district"].strip().title()
    price_usd = property_data["price_usd"]
    area_m2 = property_data["area_m2"]
    price_m2 = property_data["price_m2_usd"]
    
    # Save/Query district stats
    with Session(engine) as session:
        statement = select(DistrictStats).where(DistrictStats.district == district)
        stats = session.exec(statement).first()
        if not stats:
            # Create a new stat for this district to build the database over time
            new_stat = DistrictStats(district=district, avg_price_m2_usd=price_m2, total_properties_sampled=1)
            session.add(new_stat)
            session.commit()

    # Save the scraped property to the database
    with Session(engine) as session:
        existing_prop = session.exec(select(Property).where(Property.url == url)).first()
        if existing_prop:
            logger.info(f"Property already exists: {url}")
            return False
        
        new_prop = Property(
            url=url,
            title=property_data["title"],
            price_usd=price_usd,
            bedrooms=property_data["bedrooms"],
            bathrooms=property_data["bathrooms"],
            area_m2=area_m2,
            price_m2_usd=price_m2,
            district=district,
            description=property_data["description"],
            address=property_data["address"],
            latitude=property_data["latitude"],
            longitude=property_data["longitude"]
        )
        session.add(new_prop)
        session.commit()
        logger.info(f"Property ingested successfully: {url}")
        return True
