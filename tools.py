"""
Module containing tool implementations for web scraping and calendar integration.
"""
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """Class for handling web scraping operations."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def scrape_website(self, url: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Scrape content from a website with specified depth.
        
        Args:
            url: Website URL to scrape
            max_depth: Maximum depth for following links
            
        Returns:
            Dictionary containing scraped content and metadata
        """
        try:
            logger.info(f"Starting scrape of {url} with max_depth {max_depth}")
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content
            content = {
                'title': soup.title.string if soup.title else '',
                'text': ' '.join([p.get_text() for p in soup.find_all('p')]),
                'links': [a['href'] for a in soup.find_all('a', href=True)][:10],
                'metadata': {
                    'url': url,
                    'timestamp': datetime.now().isoformat(),
                    'status_code': response.status_code
                }
            }
            
            return {
                'status': 'success',
                'content': content
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

class CalendarTool:
    """Class for handling Google Calendar operations."""
    
    def __init__(self):
        self.credentials = None
        self.service = None
        
    def _initialize_service(self):
        """Initialize the Google Calendar service."""
        if not self.service:
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    'credentials.json', ['https://www.googleapis.com/auth/calendar.readonly']
                )
                self.service = build('calendar', 'v3', credentials=self.credentials)
            except Exception as e:
                logger.error(f"Error initializing Calendar service: {str(e)}")
                raise
                
    def fetch_calendar_events(
        self,
        calendar_id: str = 'primary',
        max_events: int = 5
    ) -> Dict[str, Any]:
        """
        Fetch events from Google Calendar.
        
        Args:
            calendar_id: ID of the calendar to fetch events from
            max_events: Maximum number of events to fetch
            
        Returns:
            Dictionary containing calendar events and metadata
        """
        try:
            self._initialize_service()
            
            now = datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=max_events,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    'summary': event.get('summary', 'No title'),
                    'start': start,
                    'description': event.get('description', ''),
                    'location': event.get('location', '')
                })
                
            return {
                'status': 'success',
                'events': formatted_events,
                'metadata': {
                    'calendar_id': calendar_id,
                    'timestamp': datetime.now().isoformat(),
                    'event_count': len(formatted_events)
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching calendar events: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Initialize global tool instances
web_scraper = WebScraper()
calendar_tool = CalendarTool()

# Expose tool functions
def scrape_website(url: str, max_depth: int = 2) -> Dict[str, Any]:
    """Wrapper function for web scraping."""
    return web_scraper.scrape_website(url, max_depth)

def fetch_calendar_events(
    calendar_id: str = 'primary',
    max_events: int = 5
) -> Dict[str, Any]:
    """Wrapper function for calendar events."""
    return calendar_tool.fetch_calendar_events(calendar_id, max_events)
