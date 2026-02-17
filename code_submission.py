import requests
from bs4 import BeautifulSoup

def get_almaty_it_news():
    url = "https://www.itnetwork.kz/news"  # пример сайта с IT новостями
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    headlines = [h.text for h in soup.find_all("h2")]
    return {
        "city": "Almaty",
        "headlines": headlines
    }
