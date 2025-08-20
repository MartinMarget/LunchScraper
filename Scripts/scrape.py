import requests
from bs4 import BeautifulSoup
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
import re
import html as html_lib
import codecs
import shutil
import importlib.util
import sys
import fitz  # PyMuPDF
from io import BytesIO
import pickle

script_dir = os.path.dirname(os.path.realpath(__file__))
print('current dir is:', os.getcwd())
print('script_dir is:', script_dir)

# Output directory for HTML files
OUTPUT_DIR = 'output'

# Template file
TEMPLATE_FILE = 'template.html'

# Restaurant table, name of restarant, URL to menu, and parser function name
def load_restaurants(config_filename):
    config_path = os.path.join(script_dir, config_filename)
    spec = importlib.util.spec_from_file_location("restaurant_config", config_path)
    config = importlib.util.module_from_spec(spec)
    sys.modules["restaurant_config"] = config
    spec.loader.exec_module(config)
    return config.RESTAURANTS

# Function to parse Trifot menu
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



def parse_menu_6(html):
    start_index = html.find('<font face="Trebuchet MS">Polévky</font>')
    end_index = html.find('<td align="left" height="25"><b><i><font face="Trebuchet MS">Saláty:</font></i></b></td>')
    text = html[start_index:end_index]         
    # Pattern for single-line items (e.g. soups)
    single_pattern = re.compile(
        r'<font face="Trebuchet MS">(\d+\.[^<]+)</font>.*?<b><i>(\d+\.-)</i></b>',
        re.DOTALL
    )

    # Pattern for two-line items (main dishes)
    multi_pattern = re.compile(
        r'<font face="Trebuchet MS">(\d+\.[^<]+)</font>.*?</td>.*?'
        r'<font face="Trebuchet MS">([^<]+)</font>.*?<font face="Trebuchet MS">(\d+\.-)</font>',
        re.DOTALL
    )

    # Find single-line items
    single_items = single_pattern.findall(text)
    start_index = html.find('<font face="Trebuchet MS">Menu</font>')
    end_index = html.find('<td align="left" height="25"><b><i><font face="Trebuchet MS">Saláty:</font></i></b></td>')
    text = html[start_index:end_index]
    # Find multi-line items
    multi_items = multi_pattern.findall(text)
 
    
    cleaned_items = []
    for name, price in single_items:
        price = price[:-2] + " Kč"  # Remove last 2 chars and add Kč
        cleaned_items.append({
            'name': name[3:],
            'price': price
        })    
    for items in multi_items:
        combined_name = items[0].strip()[3:] + " " + items[1].strip()
        price = items[2].strip()[:-2] + " Kč"  # Remove last 2 chars and add Kč
        cleaned_items.append({
            'name': combined_name,
            'price': price
        })  
    return cleaned_items


def parse_menu_8(html):
    start_index = html.find('<h3>Polévky</h3>')
    end_index = html.find('<h3>Stálá nabídka</h3>')
    text = html[start_index:end_index]         
    # Pattern for single-line items (e.g. soups)
    pattern = re.compile(
        r'<span class="field-content">([^<]+)</span>.*?'
        r'<span class="field-content">([\d, a-zA-Z]+)</span>.*?'
        r'<span class="field-content">([\d\.]+ Kč)</span>',
        re.DOTALL
    )
    matches = pattern.findall(text)
 
    cleaned_items = []
    for items in matches:
        cleaned_items.append({
            'name': items[0].strip(),
            'price': items[2].strip()
        })    
    return cleaned_items

# Function to parse AirClub menu
def parse_menu_7(html):
    html = html_lib.unescape(html) 
    today = datetime.today().strftime('%A')  # e.g. "Monday"
    if today == 'Monday':
        start_index = html.find('<span style="color: #000080;">Pondělí ')
        end_index = html.find('<span style="color: #000080;">Úterý ')
    elif today == 'Tuesday':
        start_index = html.find('<span style="color: #000080;">Úterý ')
        end_index = html.find('<span style="color: #000080;">Středa')
    elif today == 'Wednesday':
        start_index = html.find('<span style="color: #000080;">Středa')
        end_index = html.find('<span style="color: #000080;">Čtvrtek ')
    elif today == 'Thursday':
        start_index = html.find('<span style="color: #000080;">Čtvrtek ')
        end_index = html.find('<span style="color: #000080;">Pátek ')
    elif today == 'Friday':
        start_index = html.find('<span style="color: #000080;">Pátek ')
        end_index = html.find('<span style="color: #ffffff; background-color: #000080;"><strong>Menu</strong></span>')
    
    text = html[start_index:end_index]   
    pattern = re.compile(
        r'<strong>(?:<span>)?(\d+.*?)(?:</span>)?</strong>',
        re.DOTALL
    )
    
    matches = pattern.findall(text)
    cleaned_items = []
    for line in matches:
        name = line[3:-5]
        name = html_lib.unescape(name) 
        name = re.sub(r'<[^>]+>', '', name)
        name = name.strip()
        price = line[-5:-2] + " Kč"  # Extract last 3 chars and add Kč
        cleaned_items.append({
            'name': name,
            'price': price
        }) 
    return cleaned_items



# Function to parse Aspira menu
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

# Function to parse Olive menu
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

# Function to parse Theta Pub
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

def parse_menu_9(html):
    pdf_stream = download_pdf(html)
    html = extract_text_from_pdf(pdf_stream)
    today = datetime.today().strftime('%A')  # e.g. "Monday"
    if today == 'Monday':
        start_index = html.find('Pondělí: ')
        end_index = html.find('Úterý: ')
    elif today == 'Tuesday':
        start_index = html.find('Úterý: ')
        end_index = html.find('Středa: ')
    elif today == 'Wednesday':
        start_index = html.find('Středa: ')
        end_index = html.find('Čtvrtek: ')
    elif today == 'Thursday':
        start_index = html.find('Čtvrtek: ')
        end_index = html.find('Pátek: ')
    elif today == 'Friday':
        start_index = html.find('Pátek: ')
        end_index = html.find('nTabulka alergenu')
    text = html[start_index:end_index]
    pattern = re.compile(r'(\d+[,\.]?\d*\w+ [^(\n]+)')
    matches = pattern.findall(text)

    cleaned_items = []
    for item in matches:
        cleaned_items.append({
            'name': item.strip(),
            'price': "dont know, dont care"
        })
    
    return cleaned_items

def download_pdf(url):
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

def extract_text_from_pdf(pdf_stream):
    doc = fitz.open(stream=pdf_stream, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()

    return text

def fix_encoding(text):
    try:
        # Misdecoded text: try re-encoding as bytes then decoding properly
        return text.encode('latin1').decode('utf-8')
    except UnicodeDecodeError:
        return unidecode(text)  # Fallback


# Function to load menu from a restaurant URL and parse it
def load_menu(restaurant):
    try:
        resp = requests.get(restaurant['url'], timeout=10)
        resp.raise_for_status()
        parser_func = globals()[restaurant["parser"]]
        if resp.url.lower()[-3:] == "pdf":
            items = parser_func(resp.url)
        else:
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


# Function to render HTML using Jinja2   
def render_html(menu_data, restaurants_file):
    env = Environment(loader=FileSystemLoader(script_dir))
    template = env.get_template(TEMPLATE_FILE)
    menus=menu_data
    if restaurants_file == "restaurants_sona.py":
        restaurants_file = 'ThisImage2.png'
    else:
        restaurants_file = 'ThisImage.png'
    for restaurant in menus:
        print(restaurant['name'])
        for item in restaurant['items']:
            print(item['name'])
            print(item['price'])

    output = template.render(
        date=datetime.today().strftime("%A, %d.%m.%Y"),
        menus=menu_data
        , restaurants_file=restaurants_file
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding='utf-8') as f:
        f.write(output)



# Main function to load menus and render HTML
def main():
    print("Loading menus...")
    if len(sys.argv) < 2:
        print("Usage: python scrape.py <restaurants_file.py>")
        sys.exit(1)
    restaurants_file = sys.argv[1]
    RESTAURANTS = load_restaurants(restaurants_file)
    menus = [load_menu(r) for r in RESTAURANTS]
    # Save menus to a file for later use
    with open("menus.pkl", "wb") as f:
        pickle.dump(menus, f)
    render_html(menus, restaurants_file)
    print("✓ Menu summary generated: output/index.html")

if __name__ == "__main__":
    main()
