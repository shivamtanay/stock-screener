import requests
import logging
from typing import Optional, Dict
from bs4 import BeautifulSoup
import pdfplumber
import io
import time
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format
)
logger = logging.getLogger(__name__)

class StockRatingsAnalyzer:
    def __init__(self):
        # Screener.in base URL
        self.screener_base_url = "https://www.screener.in/company"
        
        # Headers to mimic browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }

    def get_page_with_playwright(self, url: str) -> str:
        """Get fully loaded page content using Playwright."""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            try:
                # Navigate to the URL
                page.goto(url)
                
                # Wait for network activity to settle
                page.wait_for_load_state("networkidle")
                
                # Additional wait for any animations or delayed content
                time.sleep(5)
                
                # Get the content
                content = page.content()
                return content
            
            finally:
                browser.close()

    def get_credit_ratings_link(self, symbol: str) -> Optional[str]:
        """
        Get the latest credit ratings link for a given stock from Screener.in.
        
        Args:
            symbol (str): Stock symbol to fetch ratings for
            
        Returns:
            Optional[str]: URL of the latest credit rating report or None if not found
        """
        try:
            # Construct URL
            url = f"{self.screener_base_url}/{symbol}/"
            logger.info(f"Fetching data from: {url}")
            
            # Make request
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find credit ratings section
            credit_ratings_section = soup.select_one('#documents > div.flex-row.flex-gap-small > div.documents.credit-ratings.flex-column > div > ul')
            
            if not credit_ratings_section:
                logger.error("Credit ratings section not found")
                return None
                
            # Get the first (latest) rating link
            latest_rating = credit_ratings_section.select_one('li:nth-child(1) > a')
            
            if not latest_rating:
                logger.error("No credit rating links found")
                return None
                
            # Extract the link
            rating_link = latest_rating.get('href')
            if not rating_link:
                logger.error("No href attribute found in rating link")
                return None
                
            # Make sure it's an absolute URL
            if not rating_link.startswith('http'):
                rating_link = f"https://www.screener.in{rating_link}"
                
            logger.info(f"Found credit rating link: {rating_link}")
            return rating_link
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from Screener.in: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def get_rating_page_text(self, rating_link: str) -> Optional[Dict]:
        """
        Get text content from the rating page and any embedded PDFs.
        If the link directly points to a PDF, only process the PDF.
        
        Args:
            rating_link (str): URL of the credit rating report
            
        Returns:
            Optional[Dict]: Dictionary containing page text and PDF text if available
        """
        try:
            # First check if the link directly points to a PDF
            response = requests.get(rating_link, headers=self.headers)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            # If it's a PDF, process it directly
            if 'application/pdf' in content_type:
                logger.info("Direct PDF link detected, processing PDF content")
                with pdfplumber.open(io.BytesIO(response.content)) as pdf:
                    pdf_text = ""
                    for page in pdf.pages:
                        pdf_text += page.extract_text() + "\n"
                return {'page_text': None, 'pdf_text': pdf_text}
            
            # If not a PDF, use Playwright to get fully loaded page
            logger.info("Using Playwright to get fully loaded page content")
            page_content = self.get_page_with_playwright(rating_link)
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # Get page text
            for script in soup(["script", "style"]):
                script.decompose()
            page_text = soup.get_text()
            lines = (line.strip() for line in page_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            page_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Look for embedded PDF in iframe within pdf_holder div
            pdf_text = None
            pdf_url = None
            
            # Find the pdf_holder div and then the iframe within it
            pdf_holder = soup.find('div', class_='pdf_holder')
            if pdf_holder:
                iframe = pdf_holder.find('iframe')
                if iframe and iframe.get('src'):
                    pdf_url = iframe.get('src')
                    # Extract the PDF ID from the URL
                    if '/Rating/ShowRationalReportFilePdf/' in pdf_url:
                        pdf_id = pdf_url.split('/')[-1]
                        # Construct the direct PDF URL
                        pdf_url = f"/Rating/GetRationalReportFilePdf?Id={pdf_id}"
            
            if pdf_url:
                if not pdf_url.startswith('http'):
                    # Get base URL from rating_link
                    base_url = '/'.join(rating_link.split('/')[:3])
                    pdf_url = f"{base_url}{pdf_url}"
                
                # Download and parse PDF
                pdf_response = requests.get(pdf_url, headers=self.headers)
                pdf_response.raise_for_status()
                
                # Verify content type is PDF
                content_type = pdf_response.headers.get('Content-Type', '').lower()
                if 'application/pdf' not in content_type:
                    logger.error(f"Expected PDF but got content type: {content_type}")
                    return {'page_text': page_text, 'pdf_text': None}
                
                # Parse PDF content
                with pdfplumber.open(io.BytesIO(pdf_response.content)) as pdf:
                    pdf_text = ""
                    for page in pdf.pages:
                        pdf_text += page.extract_text() + "\n"
            
            result = {
                'page_text': page_text,
                'pdf_text': pdf_text
            }
            
            logger.info(f"Successfully fetched page text and PDF content")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching content: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while parsing content: {str(e)}")
            return None

if __name__ == "__main__":
    # Test the function
    analyzer = StockRatingsAnalyzer()
    symbol = "PARKHOTELS"  # Test with provided symbol
    
    # Get the rating link
    rating_link = analyzer.get_credit_ratings_link(symbol)
    
    if rating_link:
        print(f"Latest credit rating link for {symbol}: {rating_link}")
        
        # Get the page text and PDF content
        content = analyzer.get_rating_page_text(rating_link)
        if content:
            if content.get('page_text'):
                print("\nPage Text:")
                print(content['page_text'][:100000] + "...")
            
            if content.get('pdf_text'):
                print("\nPDF Content:")
                print(content['pdf_text'][:100000] + "...")
            
            if not content.get('page_text') and not content.get('pdf_text'):
                print("No content available")
        else:
            print("Could not fetch content")
    else:
        print(f"Could not find credit rating link for {symbol}") 