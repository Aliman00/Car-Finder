import requests
from lxml import html

def scrape_heftelser(url):
    response = requests.get(url)
    tree = html.fromstring(response.content)
    
    # Sjekk om det finnes pant
    pant_tekst = "Det er ingen oppføringer på registreringsnummer"
    if pant_tekst in tree.text_content():
        print("Ingen heftelser funnet")
        return
    
    # Hent beløp
    belop_xpath = "//*[contains(text(), 'NOK')]"
    belop_element = tree.xpath(belop_xpath)
    if belop_element:
        print(f"Beløp: {belop_element[0].text.strip()}")
    
     # Generell XPath for alle pantsettere
    pantsettere_xpath = "/html/body/main/section/article/div[1]/div/div/div/div/div/div[1]/div/div[2]/text()"
    pantsettere = tree.xpath(pantsettere_xpath)
    for i, pantsetter in enumerate(pantsettere, 1):
        print(f"Pantsetter {i}: {pantsetter.strip()}")
    if not pantsettere:
        print("Ingen pantsettere funnet")

# Eksempel på bruk:
scrape_heftelser("https://rettsstiftelser.brreg.no/nb/oppslag/motorvogn/KJ42979")
