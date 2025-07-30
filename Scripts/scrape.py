import requests
from bs4 import BeautifulSoup
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
import re
import html
import codecs
import shutil

# Output folder


script_dir = os.path.dirname(os.path.realpath(__file__))
print('current dir is:', os.getcwd())
print('script_dir is:', script_dir)

OUTPUT_DIR = 'output'


TEMPLATE_FILE = 'template.html'

# Restaurant URLs (you'll replace these)
RESTAURANTS = [
    {
        "name": "Trifot",
        "url": "https://www.dnesniobed.cz/jidelnicek/frame/frame.php/3004_1",
        "parser": "parse_menu_alfa"
    },
    {
        "name": "Aspira",
        "url": "https://www.aspiracafe.cz/tydenni-menu/",
        "parser": "parse_menu_beta"
    },
    {
        "name": "Olive",
        "url": "https://www.olivefood.cz/coral",
        "parser": "parse_menu_gama"
    },
    {
        "name": "Pub",
        "url": "https://www.thepub.cz/praha-13",
        "parser": "parse_menu_theta"
    }
]

def parse_menu_alfa(html):
    soup = BeautifulSoup(html, 'html.parser')
    today = datetime.today().strftime('%A')  # e.g. "Monday"
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', soup.text)
   
    pattern = r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽa-záčďéěíňóřšťúůýž0-9 ,\-]+?)\s+(\d{2,3}\s*Kč)'

    matches = re.findall(pattern, cleaned)

    menu_items = [f"{name.strip()} {price.strip()}" for name, price in matches]
    menu_items[00] = re.sub(r'2025 Polévky ', '', menu_items[00])
    menu_items[1] = re.sub(r'Hlavní jídlo ', '', menu_items[1])

    # Regular expression to capture: "name" (everything before last price) and "price"
    pattern = re.compile(r'^(.*?)(\d+\s*Kč)$')

    # Final output list of dicts
    output = []

    for item in menu_items[:-9]:  # Exclude last 9 items
        match = pattern.search(item.strip())
        if match:
            name = match.group(1).strip().rstrip(',')  # trim spaces and trailing commas
            price = match.group(2).strip()
            output.append({'name': name, 'price': price})
        else:
            print(f"⚠️ Could not parse item: {item}")
    
    return output

def parse_menu_beta(html):
    today = datetime.today().strftime('%A')  # e.g. "Monday"
    if today == 'Monday':
        start_index = html.find('id="po2"')
        end_index = html.find('id="ut"')
    elif today == 'Tuesday':
        start_index = html.find('id="ut2"')
        end_index = html.find('id="st"')
    elif today == 'Wednesday':
        start_index = html.find('id="st2"')
        end_index = html.find('id="ct"')
    elif today == 'Thursday':
        start_index = html.find('id="ct2"')
        end_index = html.find('id="pa"')
    elif today == 'Friday':
        start_index = html.find('id="pa2"')
        end_index = html.find('id="pa"')
        end_index = end_index + 6000

    text = html[start_index:end_index]   
    pattern = re.compile(
        r"<div class='item-name'>(.*?)<.*?<div class='item-price'>(.*?)</div>",
        re.DOTALL
    )
    
    matches = pattern.findall(text)
    cleaned_items = []
    for name, price in matches:
        name_clean = name.replace('&nbsp;', '').strip()
        price_clean = price.replace('&nbsp;', '').strip()
        if name_clean and 'Kč' in price_clean:
            cleaned_items.append({
                'name': name_clean,
                'price': price_clean
            })
    
    return cleaned_items

def parse_menu_gama(html):
    start_index = html.find('id="dennimenu"')
    end_index = html.find('recenze-link">sem<')
    text = html[start_index:end_index]      
    raw_list = re.findall(r'<div class="dm-jidlo">(.*?)</div>', text)
    grouped = []
    for i in range(0, len(raw_list), 3):
        try:
            name_raw = raw_list[i]
            price_raw = raw_list[i+1] + ' ' + raw_list[i+2]

            name = fix_encoding(name_raw).strip()
            price = fix_encoding(price_raw).strip()

            # Optional filter to skip bad entries
            if name and "Kč" in price:
                grouped.append({
                    'name': name,
                    'price': price
                })
        except IndexError:
            continue  # Skip incomplete triplets

    return grouped


def parse_menu_theta(html):
    today = datetime.today().strftime('%A')  # e.g. "Monday"
    if today == 'Monday':
        start_index = html.find('id="menu-poledni-menu-content"')
        end_index = html.find('<h3 class="font-heading uppercase text-3xl font-bold">úterý')
    elif today == 'Tuesday':
        start_index = html.find('id="menu-poledni-menu-content"')
        end_index = html.find('<h3 class="font-heading uppercase text-3xl font-bold">středa')
    elif today == 'Wednesday':
        start_index = html.find('id="menu-poledni-menu-content"')
        end_index = html.find('<h3 class="font-heading uppercase text-3xl font-bold">čtvrtek')
    elif today == 'Thursday':
        start_index = html.find('id="menu-poledni-menu-content"')
        end_index = html.find('<h3 class="font-heading uppercase text-3xl font-bold">pátek')
    elif today == 'Friday':
        start_index = html.find('id="menu-poledni-menu-content"')
        end_index = html.find('menu-poledni-menu-perm-content')
    text = html[start_index:end_index]
    pattern = re.compile(
        r'<strong[^>]*>(.*?)<\/strong>.*?<span[^>]*>(\d+)\s*&nbsp;Kč<\/span>',
        re.DOTALL
    )
    matches = pattern.findall(text)
    cleaned_items = []
    for name, price in matches:
        cleaned_items.append({
            'name': name,
            'price': price
        })
    
    return cleaned_items

def fix_encoding(text):
    try:
        # Misdecoded text: try re-encoding as bytes then decoding properly
        return text.encode('latin1').decode('utf-8')
    except UnicodeDecodeError:
        return unidecode(text)  # Fallback

def load_menu(restaurant):
    try:
        resp = requests.get(restaurant['url'], timeout=10)
        resp.raise_for_status()
        parser_func = globals()[restaurant["parser"]]
        items = parser_func(resp.text)
        return {
            "name": restaurant["name"],
            "items": items
        }
    except Exception as e:
        return {
            "name": restaurant["name"],
            "items": [f"(Error fetching menu: {e})"]
        }
    
def generate_poll_html(question, options):
    opt = [item['name'] for item in options]
    opt.append("Nakupak")

    html = f"<form class='sticky-poll' method='post'>\n"
    html += f"<h3>{question}</h3>\n"
    
    for option in opt:
        # Each button will submit the form with its value as the chosen poll option
        html += f"<button type='submit' name='poll' value='{option}'>{option}</button>\n" 
        
    html += "</form>"
    return html

def render_html(menu_data):
    env = Environment(loader=FileSystemLoader(script_dir))
    template = env.get_template(TEMPLATE_FILE)
    menus=menu_data
    for restaurant in menus:
        print(restaurant['name'])
        for item in restaurant['items']:
            print(item['name'])
            print(item['price'])
    
    poll_html=generate_poll_html("Where do we go for lunch?", menus)

    output = template.render(
        date=datetime.today().strftime("%A, %d.%m.%Y"),
        menus=menu_data,
        poll=poll_html
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding='utf-8') as f:
        f.write(output)

def main():
    print("Loading menus...")
    menus = [load_menu(r) for r in RESTAURANTS]
    render_html(menus)
    print("✓ Menu summary generated: output/index.html")

if __name__ == "__main__":
    main()
