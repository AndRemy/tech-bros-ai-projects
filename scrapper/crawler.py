import logging
from playwright.async_api import async_playwright
from playwright_stealth import stealth

logger = logging.getLogger(__name__)

async def discover_property_links(base_url: str, max_pages: int = 2) -> list:
    """
    Crawls search result pages to discover property links.
    """
    property_links = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Apply stealth to the context
        await stealth.Stealth().apply_stealth_async(page)
        
        for page_num in range(1, max_pages + 1):
            url = f"{base_url}?page={page_num}"
            logger.info(f"Crawling page {page_num}: {url}")
            
            try:
                await page.goto(url, wait_until="domcontentloaded")
                
                # Selector for property links (needs to be adjusted based on actual Urbania structure)
                # Looking for links that point to property details
                links = await page.query_selector_all("a[href*='/inmueble/']")
                
                for link in links:
                    href = await link.get_attribute("href")
                    if href and href not in property_links:
                        # Ensure full URL
                        full_url = href if href.startswith("http") else f"https://urbania.pe{href}"
                        property_links.append(full_url)
                        
            except Exception as e:
                logger.error(f"Error crawling page {page_num}: {e}")
                
        await browser.close()
    
    logger.info(f"Discovered {len(property_links)} unique property links.")
    return property_links
