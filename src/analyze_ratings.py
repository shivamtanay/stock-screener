import logging
import re
from typing import Dict, List
import json
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

class RatingsAnalyzer:
    def __init__(self):
        self.ratings_file = "ratings.txt"
        self.analysis_file = "growth_analysis.txt"
        self.perplexity_url = "https://api.perplexity.ai/chat/completions"
        self.perplexity_token = os.getenv("PERPLEXITY_TOKEN")
        if not self.perplexity_token:
            raise ValueError("PERPLEXITY_TOKEN not found in .env file")

    def _is_company_analyzed(self, company: str) -> bool:
        """Check if analysis for the company already exists in the analysis file."""
        if not os.path.exists(self.analysis_file):
            return False
            
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for the company section in the analysis file
                return f"Company: {company}\n" in content
        except Exception as e:
            logger.error(f"Error checking analysis for {company}: {str(e)}")
            return False

    def extract_company_sections(self) -> Dict[str, str]:
        """Extract individual company sections from ratings.txt."""
        sections = {}
        current_company = None
        current_content = []
        
        try:
            with open(self.ratings_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Split content by the separator line
            company_blocks = content.split('=' * 80)
            
            for block in company_blocks:
                if not block.strip():  # Skip empty blocks
                    continue
                    
                # Extract company name from the first line
                lines = block.strip().split('\n')
                if not lines:
                    continue
                    
                # Find the line starting with 'Stock: '
                company_line = next((line for line in lines if line.startswith('Stock: ')), None)
                if not company_line:
                    continue
                    
                current_company = company_line.replace('Stock: ', '').strip()
                
                # Get all content after the company name
                content_start = block.find(company_line) + len(company_line)
                company_content = block[content_start:].strip()
                
                if current_company and company_content:
                    sections[current_company] = company_content
                    
            return sections
            
        except Exception as e:
            logger.error(f"Error reading ratings file: {str(e)}")
            return {}

    def analyze_growth_projections(self, company: str, text: str) -> Dict:
        """Analyze text for forward-looking revenue growth projections using Perplexity API."""
        # Check if analysis already exists
        if self._is_company_analyzed(company):
            logger.info(f"Analysis for {company} already exists, skipping...")
            return None

        system_prompt = """You are a financial analyst specializing in extracting forward-looking revenue growth projections from company documents. 
        Be precise and concise. Only use information explicitly stated in the provided text.
        Focus on:
        1. Future revenue growth percentages or targets
        2. Time period for these projections
        3. Exact quotes from the text as evidence
        4. Source of the projection (management/rating agency)"""

        user_prompt = f"""Analyze the following text and identify ONLY forward-looking revenue growth projections for {company}.
        
        Text to analyze:
        {text}
        
        Provide the analysis in this format:
        Company: {company}
        
        Forward-Looking Revenue Growth Projections:
        [List each projection with:
        - Projected Growth: [percentage/range]
        - Time Period: [when]
        - Evidence Quote: [exact quote]
        - Source: [management/rating agency]
        ]
        
        If no forward-looking revenue growth projections are found, respond with:
        "No forward-looking revenue growth projections found in the provided text."
        """

        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.perplexity_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.perplexity_url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            result = response.json()
            analysis = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            return {
                'company': company,
                'analysis': analysis,
                'raw_text': text
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Perplexity API for {company}: {str(e)}")
            return {
                'company': company,
                'analysis': f"Error analyzing text: {str(e)}",
                'raw_text': text
            }

    def save_analysis(self, company: str, analysis: Dict) -> None:
        """Save the analysis results to a file."""
        try:
            # Create file with header if it doesn't exist
            if not os.path.exists(self.analysis_file):
                with open(self.analysis_file, 'w', encoding='utf-8') as f:
                    f.write("Revenue Growth Projections Analysis\n")
                    f.write(f"Analysis started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*80 + "\n")

            # Append new analysis
            with open(self.analysis_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Company: {company}\n")
                f.write(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n\n")
                f.write(analysis['analysis'])
                f.write("\n\n")
        except Exception as e:
            logger.error(f"Error saving analysis for {company}: {str(e)}")

    def analyze_all_companies(self) -> None:
        """Analyze all companies in ratings.txt for growth projections."""
        # Extract company sections
        sections = self.extract_company_sections()
        if not sections:
            logger.error("No company sections found in ratings.txt")
            return
            
        logger.info(f"Found {len(sections)} companies to analyze")
        
        # Analyze each company
        for company, content in sections.items():
            logger.info(f"\nAnalyzing {company}...")
            analysis = self.analyze_growth_projections(company, content)
            if analysis:
                self.save_analysis(company, analysis)
                logger.info(f"Analysis saved for {company}")
                
        logger.info(f"\nAnalysis complete. Results saved to {self.analysis_file}")

if __name__ == "__main__":
    analyzer = RatingsAnalyzer()
    analyzer.analyze_all_companies() 