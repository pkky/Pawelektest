from flask import Flask, render_template, request
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

city_region_mapping = {
    'bialystok': 'podlaskie',
    'bydgoszcz': 'kujawsko--pomorskie',
    'gdansk': 'pomorskie',
    'gorzow-wielkopolski': 'lubuskie',
    'katowice': 'slaskie',
    'kielce': 'swietokrzyskie',
    'krakow': 'malopolskie',
    'lublin': 'lubelskie',
    'lodz': 'lodzkie',
    'olsztyn': 'warminsko--mazurskie',
    'opole': 'opolskie',
    'poznan': 'wielkopolskie',
    'rzeszow': 'podkarpackie',
    'szczecin': 'zachodniopomorskie',
    'torun': 'kujawsko-pomorskie',
    'warszawa': 'mazowieckie',
    'wroclaw': 'dolnoslaskie',
    'zielona-gora': 'lubuskie'
}

urls = {
    'renting_houses': 'https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/{region}/{city}/{city}?ownerTypeSingleSelect=ALL&distanceRadius=0&viewType=listing&page={page}',
}

@app.route('/', methods=['GET'])
async def index():
    city = request.args.get('city', 'warszawa').replace(" ", "").lower()
    page = request.args.get('page', 1, type=int)
    region = city_region_mapping.get(city, 'mazowieckie')

    base_url = urls['renting_houses'].format(region=region, city=city, page=page)

    async with aiohttp.ClientSession() as session:
        room_links = await get_room_links_from_pages(base_url, 1, session)
        rooms_data = await asyncio.gather(*[get_coordinates_and_content(link, session) for link in set(room_links)])

    next_page = page + 1

    city_coords = {
        "warszawa": [52.229676, 21.012229],
        "lodz": [51.759445, 19.457216],
        "krakow": [50.064651, 19.944981],
        "wroclaw": [51.107883, 17.038538],
        "bydgoszcz": [53.123482, 18.008438],
        "torun": [53.013790, 18.598444],
        "lublin": [51.246454, 22.568446],
        "gorzow-wielkopolski": [52.73679, 15.22878],
        "zielona-gora": [51.935621, 15.506186],
        "opole": [50.675107, 17.921298],
        "rzeszow": [50.041187, 21.999121],
        "bialystok": [53.132489, 23.168840],
        "gdansk": [54.352025, 18.646638],
        "katowice": [50.270908, 19.039993],
        "kielce": [50.866077, 20.628569],
        "olsztyn": [53.770226, 20.490189],
        "poznan": [52.406374, 16.925168],
        "szczecin": [53.428543, 14.552812]
    }

    return render_template('index.html', cities=city_region_mapping.keys(), selected_city=city, rooms_data=rooms_data, current_page=page, next_page=next_page, city_coords=city_coords)

async def get_room_links_from_pages(base_url, num_pages, session):
    room_links = []
    for page_num in range(1, num_pages + 1):
        page_url = f'{base_url}&strona={page_num}'
        async with session.get(page_url) as response:
            page_content = await response.text()
            room_links.extend(extract_room_links(page_content))
    return room_links

def extract_room_links(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        if a['href'].startswith('/pl/oferta/'):
            full_link = 'https://www.otodom.pl' + a['href']
            links.add(full_link)
    return list(links)

async def get_coordinates_and_content(room_url, session):
    async with session.get(room_url) as response:
        page_content = await response.text()
    
    soup = BeautifulSoup(page_content, 'html.parser')
    coordinates_script = soup.find('script', string=re.compile(r'"latitude":([0-9.]+),"longitude":([0-9.]+)'))
    lat, lng = None, None
    if coordinates_script:
        match = re.search(r'"latitude":([0-9.]+),"longitude":([0-9.]+)', coordinates_script.string)
        if match:
            lat, lng = match.groups()

    name = soup.find('h1', class_='css-1wnihf5 efcnut38').get_text().strip() if soup.find('h1', class_='css-1wnihf5 efcnut38') else 'No Name'
    price = soup.find('strong', class_='css-t3wmkv e1l1avn10').get_text().strip() if soup.find('strong', class_='css-t3wmkv e1l1avn10') else 'No Price'
    surface = soup.find('div', class_='css-1wi2w6s enb64yk5').get_text().strip() if soup.find('div', class_='css-1wi2w6s enb64yk5') else 'No Surface Info'
    
    return {
        'latitude': lat,
        'longitude': lng,
        'name': name,
        'price': price,
        'surface': surface,
        'link': room_url
    }

if __name__ == '__main__':
    app.run(debug=True, port=5001)