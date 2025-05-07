import requests
from bs4 import BeautifulSoup
import json
import os
import re

# Directory to save name data files
SAVE_DIR = "world/wod20th/data/names"

# Create directory if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)

# URLs for name lists
NAME_URLS = {
    "american": "http://eakett.ca/sgnp/contemporary/american.htm",
    "arabic": "http://eakett.ca/sgnp/contemporary/arabic.htm",
    "brazilian": "http://eakett.ca/sgnp/contemporary/brazilian.htm",
    "chechen": "http://eakett.ca/sgnp/contemporary/chechen.htm",
    "chinese": "http://eakett.ca/sgnp/contemporary/chinese.htm",
    "czech": "http://eakett.ca/sgnp/contemporary/czech.htm",
    "danish": "http://eakett.ca/sgnp/contemporary/danish.htm",
    "filipino": "http://eakett.ca/sgnp/contemporary/filipino.htm",
    "finnish": "http://eakett.ca/sgnp/contemporary/finnish.htm",
    "french": "http://eakett.ca/sgnp/contemporary/french.htm",
    "german": "http://eakett.ca/sgnp/contemporary/german.htm",
    "greek": "http://eakett.ca/sgnp/contemporary/greek.htm",
    "hungarian": "http://eakett.ca/sgnp/contemporary/hungarian.htm",
    "irish": "http://eakett.ca/sgnp/contemporary/irish.htm",
    "italian": "http://eakett.ca/sgnp/contemporary/italian.htm",
    "jamaican": "http://eakett.ca/sgnp/contemporary/jamiacan.htm",
    "japanese": "http://eakett.ca/sgnp/contemporary/japanese.htm",
    "korean": "http://eakett.ca/sgnp/contemporary/korean.htm",
    "mongolian": "http://eakett.ca/sgnp/contemporary/mongolian.htm",
    "north_indian": "http://eakett.ca/sgnp/contemporary/north_indian.htm",
    "portuguese": "http://eakett.ca/sgnp/contemporary/portuguese.htm",
    "prison": "http://eakett.ca/sgnp/contemporary/prison.htm",
    "roma": "http://eakett.ca/sgnp/contemporary/roma.htm",
    "russian": "http://eakett.ca/sgnp/contemporary/russian.htm",
    "senegalese": "http://eakett.ca/sgnp/contemporary/senegalese.htm",
    "sicilian": "http://eakett.ca/sgnp/contemporary/sicilian.htm",
    "spanish": "http://eakett.ca/sgnp/contemporary/spanish.htm",
    "thai": "http://eakett.ca/sgnp/contemporary/thai.htm",
    "united_kingdom": "http://eakett.ca/sgnp/contemporary/united_kingdom.htm",
    "nahuatl": "http://eakett.ca/sgnp/historical/aztec.htm",
    "persian": "http://eakett.ca/sgnp/historical/persian.htm",
    "polish": "http://eakett.ca/sgnp/historical/polish.htm",
    "polynesian": "http://eakett.ca/sgnp/historical/polynesian.htm",
    "maori": "http://eakett.ca/sgnp/historical/maori.htm",
    "vietnamese": "http://eakett.ca/sgnp/new_names_2012/vietnamese.htm",
    "slovene": "http://eakett.ca/sgnp/new_names_2012/modern_slovene.htm"
}

def extract_name_lists(html_content):
    """
    Extract name lists from the HTML content of a story games name project page.
    Returns a dictionary with first names (male and female) and last names.
    
    The function handles multiple possible formats of the name lists.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find tables that contain the name data
    tables = soup.find_all('table')
    
    result = {}
    male_first_names = []
    female_first_names = []
    last_names = []
    generic_first_names = []
    
    # Process each table to extract names
    for table in tables:
        # Try to determine what kind of names this table contains
        table_text = table.get_text().lower()
        
        # Check if this table contains male or female names or surnames
        is_male = any(keyword in table_text for keyword in ['male', 'men', 'boy'])
        is_female = any(keyword in table_text for keyword in ['female', 'women', 'girl'])
        is_last_name = any(keyword in table_text for keyword in ['surname', 'last name', 'family'])
        
        # Extract names from rows
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            
            # Skip header rows or empty rows
            if not cells:
                continue
                
            # Extract names from cells
            for cell in cells:
                name = cell.get_text().strip()
                
                # Skip empty cells or cells with just numbers
                if not name or re.match(r'^\d+$', name):
                    continue
                
                # Check for roll indicators (like "Roll 1-20" or similar)
                if re.search(r'roll|^\d+-\d+$', name.lower()):
                    continue
                    
                # Clean the name
                name = re.sub(r'\d+\.?\s*', '', name)  # Remove numbering
                name = name.strip()
                
                if not name:
                    continue
                
                # Add name to appropriate list
                if is_last_name:
                    last_names.append(name)
                elif is_male:
                    male_first_names.append(name)
                elif is_female:
                    female_first_names.append(name)
                else:
                    generic_first_names.append(name)
    
    # If we found specific gender names, add them to the result
    if male_first_names:
        result["male_first"] = male_first_names
    if female_first_names:
        result["female_first"] = female_first_names
    
    # If we found generic first names, add them
    if generic_first_names:
        result["first_names"] = generic_first_names
    
    # Add last names
    if last_names:
        result["last_names"] = last_names
    
    return result

def scrape_all_name_lists():
    """
    Scrape all name lists from the URLs and save them as JSON files.
    """
    print(f"Starting to scrape {len(NAME_URLS)} name lists...")
    
    for nationality, url in NAME_URLS.items():
        print(f"Scraping {nationality} names from {url}")
        
        try:
            # Download the page
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Failed to download {url}: Status code {response.status_code}")
                continue
                
            # Extract name lists
            name_data = extract_name_lists(response.text)
            
            # Check if we got any data
            if not name_data:
                print(f"No name data found for {nationality}")
                continue
                
            # Save as JSON
            file_path = os.path.join(SAVE_DIR, f"{nationality}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(name_data, f, ensure_ascii=False, indent=2)
                
            print(f"Saved {nationality} name data to {file_path}")
            print(f"  - Male first names: {len(name_data.get('male_first', []))}")
            print(f"  - Female first names: {len(name_data.get('female_first', []))}")
            print(f"  - Generic first names: {len(name_data.get('first_names', []))}")
            print(f"  - Last names: {len(name_data.get('last_names', []))}")
            
        except Exception as e:
            print(f"Error scraping {nationality}: {e}")
    
    print("Scraping complete!")

if __name__ == "__main__":
    scrape_all_name_lists()
