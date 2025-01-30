import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import logging
import argparse
import re

class WebCrawler:
    def __init__(self, base_url, output_file, delay=1):
        """
        Initialize the web crawler
        
        Args:
            base_url (str): The starting URL to crawl
            output_file (str): Path to save the extracted text
            delay (int): Delay between requests in seconds
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.output_file = output_file
        self.delay = delay
        self.visited_urls = set()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # Common patterns for navigation, header, and footer content
        self.nav_patterns = {
            'tags': {'nav', 'header', 'footer'},
            'classes': {'navigation', 'nav', 'navbar', 'menu', 'header', 'footer', 'bottom'},
            'ids': {'navigation', 'nav', 'navbar', 'menu', 'header', 'footer', 'bottom'},
        }

    def is_valid_url(self, url):
        """Check if URL belongs to the same domain and hasn't been visited"""
        parsed = urlparse(url)
        return (
            parsed.netloc == self.domain and
            url not in self.visited_urls and
            not url.endswith(('.pdf', '.jpg', '.png', '.gif'))
        )

    def is_navigation_element(self, element):
        """
        Check if an element is likely to be navigation, header, or footer content
        """
        if not element or not hasattr(element, 'name'):
            return False
            
        if element.name in self.nav_patterns['tags']:
            return True

        try:
            # Check classes
            element_classes = {c.lower() for c in element.get('class', [])} if element.get('class') else set()
            if any(pattern in element_classes for pattern in self.nav_patterns['classes']):
                return True

            # Check id
            element_id = str(element.get('id', '')).lower()
            if any(pattern in element_id for pattern in self.nav_patterns['ids']):
                return True

            # Check common patterns in class names and IDs
            for attr in ['class', 'id']:
                value = element.get(attr, '')
                if value is None:
                    continue
                if isinstance(value, list):
                    value = ' '.join(value)
                value = str(value).lower()
                if any(pattern in value for pattern in ['nav', 'menu', 'header', 'footer']):
                    return True

        except (AttributeError, TypeError):
            return False

        return False

    def extract_text(self, soup):
        """Extract readable text from the webpage while excluding navigation elements"""
        if not soup:
            return ""
            
        try:
            # Remove script and style elements
            for element in soup(['script', 'style', 'head', 'noscript', 'iframe']):
                if element:
                    element.decompose()

            # Remove navigation, header, and footer elements
            for element in soup.find_all():
                if self.is_navigation_element(element):
                    element.decompose()

            # Find the main content area (if it exists)
            main_content = None
            try:
                main_content = soup.find(['main', 'article']) or soup.find(class_=re.compile(r'content|main|article'))
            except (AttributeError, TypeError):
                pass

            # If we found a main content area, use that; otherwise use the whole soup
            content = main_content if main_content else soup
            
            # Get text and clean it up
            if not content:
                return ""
                
            text = content.get_text(separator=' ')
            if not text:
                return ""
                
            # Clean up whitespace
            text = ' '.join(text.split())
            
            # Remove any lines that are likely navigation items
            lines = text.split('\n')
            cleaned_lines = [line for line in lines 
                            if len(line.split()) > 3  # Skip very short lines
                            and not any(nav in line.lower() 
                                      for nav in ['menu', 'navigation', 'skip to content'])]
            
            return '\n'.join(cleaned_lines)
            
        except (AttributeError, TypeError) as e:
            self.logger.warning(f"Error extracting text: {str(e)}")
            return ""

    def get_links(self, soup, current_url):
        """Extract all valid links from the page"""
        links = set()
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(current_url, href)
                if self.is_valid_url(absolute_url):
                    links.add(absolute_url)
        return links

    def crawl(self):
        """Start the crawling process"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                self._crawl_url(self.base_url, f)
            self.logger.info(f"Crawling completed. Visited {len(self.visited_urls)} pages.")
        except Exception as e:
            self.logger.error(f"Crawling failed: {str(e)}")

    def _crawl_url(self, url, file):
        """Recursively crawl URLs and save text content"""
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        self.logger.info(f"Crawling: {url}")
        
        try:
            # Add delay to be respectful to the server
            time.sleep(self.delay)
            
            # Fetch and parse the page
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract and save text
            text = self.extract_text(soup)
            if text.strip():  # Only write if we have meaningful content
                file.write(f"\n\n=== Content from: {url} ===\n")
                file.write(text)
            
            # Get links and crawl them
            links = self.get_links(soup, url)
            for link in links:
                self._crawl_url(link, file)
                
        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Web crawler to extract text from websites')
    parser.add_argument('url', help='The base URL to start crawling from')
    parser.add_argument('-o', '--output', default='crawled_text.txt',
                      help='Output file path (default: crawled_text.txt)')
    parser.add_argument('-d', '--delay', type=float, default=1.0,
                      help='Delay between requests in seconds (default: 1.0)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create and run crawler
    crawler = WebCrawler(args.url, args.output, args.delay)
    crawler.crawl()

if __name__ == "__main__":
    main()