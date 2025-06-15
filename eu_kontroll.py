import requests
from lxml import html

def scrape_eu_kontroll(registration_number: str):
    """
    Scrape EU-kontroll information for a given registration number from vegvesen.no
    """
    try:
        url = f"https://www.vegvesen.no/kjoretoy/kjop-og-salg/kjoretoyopplysninger/sjekk-kjoretoyopplysninger?registreringsnummer={registration_number}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        tree = html.fromstring(response.content)
        
        eu_kontroll_info = {
            "sist_godkjent": None,
            "frist_neste_kontroll": None
        }

        print("Scraping EU-kontroll information...")
        
        # For sist godkjent
        sist_elements = tree.xpath("/html/body/main/div[1]/div/div/div[4]/div/div/div[1]/div[3]/div[1]/div/dl[1]/dd")
        print(f"Found {len(sist_elements)} elements for 'sist godkjent'")
        if sist_elements:
            sist_godkjent_tekst = sist_elements[0].text_content().strip()

        # For frist neste kontroll  
        frist_elements = tree.xpath("/html/body/main/div[1]/div/div/div[4]/div/div/div[1]/div[3]/div[1]/div/dl[2]/dd")
        print(f"Found {len(frist_elements)} elements for 'frist neste kontroll'")
        if frist_elements:
            frist_tekst = frist_elements[0].text_content().strip()
                
        return eu_kontroll_info
        
    except:
        return {
            "sist_godkjent": None,
            "frist_neste_kontroll": None
        }

# Test
if __name__ == "__main__":
    result = scrape_eu_kontroll("BD57802")
    print(result)