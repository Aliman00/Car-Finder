import asyncio
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
import requests
from bs4 import BeautifulSoup
import re

app = Server("web_scraper")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="fetch_finn_data",
            description="Fetch and parse car data from Finn.no URLs",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Finn.no search URL"},
                    "max_pages": {"type": "integer", "default": 1, "description": "Maximum pages to scrape"}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="extract_car_details",
            description="Extract detailed information from a specific car listing",
            inputSchema={
                "type": "object", 
                "properties": {
                    "car_url": {"type": "string", "description": "Direct URL to car listing"}
                },
                "required": ["car_url"]
            }
        )
    ]

# This function is called when a tool is invoked
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "fetch_finn_data":
        return await fetch_finn_data(arguments["url"], arguments.get("max_pages", 1))
    elif name == "extract_car_details":
        return await extract_car_details(arguments["car_url"])


# This function fetches car data from Finn.no and parses it
async def fetch_finn_data(url: str, max_pages: int = 1):
    """Enhanced version of your parse_car_data function"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        all_cars = []
        current_year = 2025
        
        for page in range(max_pages):
            page_url = f"{url}&page={page + 1}" if page > 0 else url
            response = requests.get(page_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            cars = parse_page_cars(soup, current_year)
            all_cars.extend(cars)
            
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "cars_found": len(all_cars),
                "data": all_cars
            }, ensure_ascii=False)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text", 
            text=json.dumps({"success": False, "error": str(e)})
        )]

def parse_page_cars(soup, current_year):
    """Your existing parsing logic from main.py"""
    parsed_cars_list = []
    successful_car_id_counter = 0

    # Find the main tag with a class that starts with "page-container"
    main_element = soup.find('main', class_=re.compile(r"page-container"))
    if not main_element:
        return []

    # CSS selector to navigate to the container of car listings
    ads_container_selector = 'div:nth-of-type(1) > div:nth-of-type(2) > section > div:nth-of-type(3)'
    ads_container = main_element.select_one(ads_container_selector)
    if not ads_container:
        return []

    # Get all direct div children of ads_container
    car_item_wrapper_divs = ads_container.find_all('div', recursive=False)
    if not car_item_wrapper_divs:
        return []

    # Iterate through potential car ad wrappers
    for car_wrapper_div in car_item_wrapper_divs: 
        article_element = car_wrapper_div.find('article', recursive=False)
        if not article_element:
            article_element = car_wrapper_div.find('article') 
            if not article_element:
                continue
        
        # Initialize dictionary for this potential car
        car_info = {
            'name': None,
            'link': None,
            'image_url': None,
            'additional_info': None,
            'year': None,
            'mileage': None,
            'price': None,
            'age': None,
            'km_per_year': None
        }

        # Image URL
        image_tag = article_element.select_one('div:nth-of-type(2) > div > img')
        if image_tag:
            car_info['image_url'] = image_tag.get('src') or image_tag.get('data-src')

        # Main info container
        info_div = article_element.select_one('div:nth-of-type(3)')
        
        if info_div:
            # Car Name (Model) and Ad Link
            name_tag = info_div.find('h2')
            if name_tag:
                car_info['name'] = name_tag.get_text(strip=True)
                link_tag = name_tag.find('a')
                if link_tag and link_tag.has_attr('href'):
                    ad_url = link_tag['href']
                    if ad_url.startswith('/'):
                        base_url = "https://www.finn.no"
                        ad_url = base_url + ad_url
                    car_info['link'] = ad_url

            # Additional Info
            additional_info_tag = info_div.find('span', class_='text-caption')
            if additional_info_tag:
                car_info['additional_info'] = additional_info_tag.get_text(strip=True)

            # Year and Mileage details
            details_tag = info_div.select_one('span:nth-of-type(2)')
            if details_tag:
                details_text = details_tag.get_text(strip=True)
                
                year_match = re.search(r'\b(19\d{2}|20\d{2})\b', details_text)
                if year_match:
                    year_str = year_match.group(0)
                    if year_str.isdigit():
                        car_info['year'] = int(year_str)
                        car_info['age'] = current_year - car_info['year']
                
                mileage_match = re.search(r'(\d[\d\s.,]*\s*km)\b', details_text, re.IGNORECASE)
                if mileage_match:
                    raw_mileage_text = mileage_match.group(1)
                    mileage_str_cleaned = re.sub(r'[^\d]', '', raw_mileage_text.lower().replace('km', ''))
                    if mileage_str_cleaned.isdigit():
                        car_info['mileage'] = int(mileage_str_cleaned)

            # Calculate km_per_year
            if car_info['mileage'] is not None and car_info['age'] is not None:
                if car_info['age'] > 0:
                    car_info['km_per_year'] = round(car_info['mileage'] / car_info['age'])
                elif car_info['age'] == 0:
                    car_info['km_per_year'] = car_info['mileage'] 
            
            # Price
            price_tag = info_div.select_one('div:nth-of-type(1)')
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                if "solgt" in price_text.lower():
                    car_info['price'] = "Solgt"
                else:
                    price_digits = re.sub(r'[^\d]', '', price_text)
                    if price_digits:
                        car_info['price'] = int(price_digits)

        # Only add to list if essential data like name was found
        if car_info.get('name'): 
            successful_car_id_counter += 1
            car_info['id'] = successful_car_id_counter
            parsed_cars_list.append(car_info)

    return parsed_cars_list


# This function extracts detailed information from a specific car listing URL
async def extract_car_details(car_url: str):
    """Extract detailed information from individual car listing"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(car_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Extract detailed car information
        details = {
            "url": car_url,
            "title": None,
            "description": None,
            "specifications": {},
            "equipment": []
            # "seller_info": {}
        }
        
        # Extract title
        title_tag = soup.find('h1')
        if title_tag:
            details["title"] = title_tag.get_text(strip=True)
        
        # Find the main content area
        main_content = soup.find('main')
        if main_content:
            # Look for all sections
            sections = main_content.find_all('section')
            
            for i, section in enumerate(sections):
                section_text = section.get_text(strip=True).lower()
                
                # Extract Description (Beskrivelse) - section[1]
                if 'beskrivelse' in section_text or 'description' in section_text:
                    description = extract_description_from_section(section)
                    if description:
                        details["description"] = description
                
                # Extract Specifications (Spesifikasjoner) - section[2]
                elif 'spesifikasjoner' in section_text or 'specifications' in section_text:
                    specs = extract_specifications_from_section(section)
                    details["specifications"].update(specs)
                
                # Extract Equipment (Utstyr) - section[3]
                elif 'utstyr' in section_text or 'equipment' in section_text:
                    equipment = extract_equipment_from_section(section)
                    details["equipment"].extend(equipment)
                
                # Extract seller info
                # elif 'selger' in section_text or 'dealer' in section_text or 'forhandler' in section_text:
                #     seller_info = extract_seller_info_from_section(section)
                #     details["seller_info"].update(seller_info)
        
        # Alternative approach - look for specific data structures
        if not details["specifications"]:
            # Look for key-value pairs in various formats
            specs = extract_specifications_alternative(soup)
            details["specifications"].update(specs)
        
        if not details["equipment"]:
            # Look for equipment lists
            equipment = extract_equipment_alternative(soup)
            details["equipment"].extend(equipment)
            
        return [TextContent(
            type="text",
            text=json.dumps(details, ensure_ascii=False)
        )]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e), "url": car_url})
        )]

def extract_description_from_section(section):
    """Extract description text from a beskrivelse section"""
    description = None
    
    # Method 1: Look for paragraphs in the section
    paragraphs = section.find_all('p')
    if paragraphs:
        # Combine all paragraphs
        desc_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and text.lower() != 'beskrivelse':  # Skip the header
                desc_parts.append(text)
        if desc_parts:
            description = ' '.join(desc_parts)
    
    # Method 2: Look for divs with text content
    if not description:
        divs = section.find_all('div')
        for div in divs:
            text = div.get_text(strip=True)
            if text and len(text) > 20 and text.lower() != 'beskrivelse':
                # Check if this div doesn't have many nested elements (likely pure text)
                nested_elements = len(div.find_all(['div', 'span', 'p']))
                if nested_elements <= 2:  # Allow some nesting but not too much
                    description = text
                    break
    
    # Method 3: Get all text from section excluding header
    if not description:
        all_text = section.get_text(strip=True)
        # Remove the "Beskrivelse" header if it's at the beginning
        if all_text.lower().startswith('beskrivelse'):
            description = all_text[11:].strip()  # Remove "beskrivelse" and clean
        elif len(all_text) > 20:
            description = all_text
    
    return description if description and len(description) > 10 else None

def extract_specifications_from_section(section):
    """Extract specifications from a section element"""
    specs = {}
    
    # Look for definition lists (dl/dt/dd structure)
    dl_elements = section.find_all('dl')
    for dl in dl_elements:
        dt_elements = dl.find_all('dt')
        dd_elements = dl.find_all('dd')
        
        for dt, dd in zip(dt_elements, dd_elements):
            key = dt.get_text(strip=True)
            value = dd.get_text(strip=True)
            if key and value:
                specs[key] = value
    
    # Look for table structures
    tables = section.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if key and value:
                    specs[key] = value
    
    # Look for div pairs or similar structures
    divs = section.find_all('div')
    for i in range(0, len(divs) - 1, 2):
        if i + 1 < len(divs):
            potential_key = divs[i].get_text(strip=True)
            potential_value = divs[i + 1].get_text(strip=True)
            
            # Check if this looks like a key-value pair
            if (len(potential_key) < 50 and len(potential_value) < 200 and 
                ':' not in potential_key and potential_key and potential_value):
                specs[potential_key] = potential_value
    
    return specs

def extract_equipment_from_section(section):
    """Extract equipment list from a section element"""
    equipment = []
    
    # Look for unordered/ordered lists
    lists = section.find_all(['ul', 'ol'])
    for ul in lists:
        items = ul.find_all('li')
        for item in items:
            text = item.get_text(strip=True)
            if text and len(text) < 100:  # Avoid very long text that's not equipment
                equipment.append(text)
    
    # Look for divs that might contain equipment items
    divs = section.find_all('div')
    for div in divs:
        text = div.get_text(strip=True)
        # Check if this looks like an equipment item (short, descriptive text)
        if (text and len(text.split()) <= 5 and len(text) < 50 and 
            not any(char.isdigit() for char in text[:10])):  # Avoid specs that start with numbers
            if text not in equipment:  # Avoid duplicates
                equipment.append(text)
    
    return equipment

# def extract_seller_info_from_section(section):
#     """Extract seller information from a section element"""
#     seller_info = {}
    
#     # Look for common seller info patterns
#     seller_patterns = {
#         'name': ['navn', 'name', 'forhandler', 'dealer'],
#         'phone': ['telefon', 'tlf', 'phone'],
#         'email': ['e-post', 'email'],
#         'address': ['adresse', 'address'],
#         'location': ['sted', 'location', 'by']
#     }
    
#     section_text = section.get_text()
    
#     # Extract phone numbers
#     phone_match = re.search(r'(\+47\s?)?(\d{2}\s?\d{2}\s?\d{2}\s?\d{2})', section_text)
#     if phone_match:
#         seller_info['phone'] = phone_match.group(0)
    
#     # Extract email addresses
#     email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', section_text)
#     if email_match:
#         seller_info['email'] = email_match.group(0)
    
#     # Look for other seller info in structured format
#     for info_type, patterns in seller_patterns.items():
#         for pattern in patterns:
#             # Look for pattern followed by colon and value
#             match = re.search(rf'{pattern}[:\s]+([^\n\r]+)', section_text, re.IGNORECASE)
#             if match:
#                 seller_info[info_type] = match.group(1).strip()
#                 break
    
#     return seller_info
 
def extract_specifications_alternative(soup):
    """Alternative method to extract specifications if section-based approach fails"""
    specs = {}
    
    # Look for any element that might contain specifications
    spec_keywords = ['motor', 'drivstoff', 'girkasse', 'hjuldrift', 'årsmodell', 'kilometer', 
                    'effekt', 'sylindre', 'co2', 'forbruk', 'toppfart', 'acceleration']
    
    for keyword in spec_keywords:
        # Look for text that contains the keyword followed by a value
        pattern = rf'{keyword}[:\s]*([^\n\r,]+)'
        matches = re.findall(pattern, soup.get_text(), re.IGNORECASE)
        if matches:
            specs[keyword.capitalize()] = matches[0].strip()
    
    return specs

def extract_equipment_alternative(soup):
    """Alternative method to extract equipment if section-based approach fails"""
    equipment = []
    
    # Common Norwegian car equipment terms
    equipment_keywords = [
        'klimaanlegg', 'aircondition', 'cruisecontrol', 'navigasjon', 'gps',
        'bluetooth', 'dab', 'radio', 'cd', 'mp3', 'usb', 'aux',
        'elektriske', 'oppvarming', 'kjøling', 'automatisk', 'manuell',
        'sportsseter', 'skinnseter', 'elektrisk', 'parkeringssensor',
        'ryggekamera', 'xenon', 'led', 'tåkelys', 'metallic', 'felger'
    ]
    
    soup_text = soup.get_text().lower()
    
    for keyword in equipment_keywords:
        if keyword in soup_text:
            # Try to extract the full equipment name around the keyword
            pattern = f'([^.\n]*{keyword}[^.\n]*)'
            matches = re.findall(pattern, soup_text, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip()
                if 10 < len(clean_match) < 50:  # Reasonable length for equipment item
                    equipment.append(clean_match.capitalize())
    
    return list(set(equipment))  # Remove duplicates

""" if __name__ == "__main__":
    import sys
    from mcp.server.stdio import stdio_server
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream, 
                write_stream, 
                app.create_initialization_options()
            )
    
    asyncio.run(main()) """

