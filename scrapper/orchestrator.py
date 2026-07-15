import asyncio
import logging
from scrapper.crawler import discover_property_links
from ingestion.ingestor import ingest_property_link

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pipeline(base_search_url: str, max_pages: int = 1):
    """
    Orchestrates the scraping pipeline: Discover links -> Ingest.
    """
    logger.info("Starting scraping pipeline...")
    
    # 1. Producer: Discover links
    property_links = await discover_property_links(base_search_url, max_pages=max_pages)
    
    # 2. Consumer: Ingest links
    # For simplicity, we process sequentially for now. 
    # Can be optimized to use a queue for parallel processing later.
    for i, link in enumerate(property_links):
        logger.info(f"Processing ({i+1}/{len(property_links)}): {link}")
        success = ingest_property_link(link)
        if success:
            logger.info(f"Successfully ingested: {link}")
        else:
            logger.warning(f"Failed to ingest: {link}")
            
    logger.info("Scraping pipeline completed.")

if __name__ == "__main__":
    # Example URL (ensure this is a valid search result URL)
    search_url = "https://urbania.pe/inmueble/venta/departamento/miraflores"
    asyncio.run(run_pipeline(search_url, max_pages=1))
