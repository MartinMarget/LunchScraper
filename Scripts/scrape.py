import requests
from bs4 import BeautifulSoup
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
import re

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))
OUTPUT_DIR = 'output'
TEMPLATE_FILE = 'template.html' # Assuming this template is also in the script_dir

# List of restaurants to scrape
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
    """
    Parses the menu for 'Trifot' restaurant.
    Extracts menu items and prices using regex.
    """
    soup = BeautifulSoup(html, 'html.parser')
    # Replace multiple whitespaces with a single space for easier regex matching
    cleaned = re.sub(r'\s+', ' ', soup.text)
    # Regex pattern to find menu item names (including Czech characters) and prices
    pattern = r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽa-záčďéěíňóřšťúůýž0-9 ,\-]+?)\s+(\d{2,3}\s*Kč)'
    matches = re.findall(pattern, cleaned)
    menu_items = [f"{name.strip()} {price.strip()}" for name, price in matches]

    # Specific cleaning for Trifot's first few items
    if len(menu_items) > 0:
        menu_items[0] = re.sub(r'2025 Polévky ', '', menu_items[0])
    if len(menu_items) > 1:
        menu_items[1] = re.sub(r'Hlavní jídlo ', '', menu_items[1])

    # Pattern to separate name and price from combined string
    item_price_pattern = re.compile(r'^(.*?)(\d+\s*Kč)$')
    output = []
    # Slice the list, ensuring it doesn't go out of bounds
    slice_end = len(menu_items) - 9 if len(menu_items) > 9 else 0
    for item in menu_items[:slice_end]:
        match = item_price_pattern.search(item.strip())
        if match:
            name = match.group(1).strip().rstrip(',')
            price = match.group(2).strip()
            output.append({'name': name, 'price': price})
    return output

def parse_menu_beta(html):
    """
    Parses the menu for 'Aspira' restaurant based on the current day.
    """
    today = datetime.today().strftime('%A') # e.g., 'Monday'
    
    # Mapping of English day names to HTML IDs for Aspira's menu sections
    day_start_ids = {
        'Monday': 'po2',
        'Tuesday': 'ut2',
        'Wednesday': 'st2',
        'Thursday': 'ct2',
        'Friday': 'pa2'
    }
    # Mapping of English day names to HTML IDs for the *next* day's section, used as end marker
    day_end_ids = {
        'Monday': 'ut',
        'Tuesday': 'st',
        'Wednesday': 'ct',
        'Thursday': 'pa',
        'Friday': 'pa' # For Friday, the end marker might be the same as the start of the next section, or just a large offset
    }

    start_id = day_start_ids.get(today)
    end_id = day_end_ids.get(today)

    if not start_id:
        return [] # No menu for today or invalid day

    start_index = html.find(f'id="{start_id}"')
    
    # Handle cases where start_index is not found
    if start_index == -1:
        return []

    end_index = html.find(f'id="{end_id}"')

    # Special handling for Friday or if the next day's marker isn't found
    if today == 'Friday' or end_index == -1:
        # If 'pa' is the last day, or next day not found, extend search to cover full section
        # This is a heuristic and might need adjustment based on actual HTML structure
        end_index = html.find('id="pa"') + 6000 # Extend search for Friday's end, or until a large offset

    # Ensure valid slice range
    if start_index >= end_index: # If end_index is before start_index or not found effectively
        text = html[start_index:] # Take from start to end of document
    else:
        text = html[start_index:end_index]

    # Regex to find item names and prices within the extracted HTML segment
    pattern = re.compile(r"<div class='item-name'>(.*?)<.*?<div class='item-price'>(.*?)</div>", re.DOTALL)
    matches = pattern.findall(text)
    cleaned_items = []
    for name, price in matches:
        name_clean = name.replace('&nbsp;', '').strip()
        price_clean = price.replace('&nbsp;', '').strip()
        if name_clean and 'Kč' in price_clean:
            cleaned_items.append({'name': name_clean, 'price': price_clean})
    return cleaned_items

def parse_menu_gama(html):
    """
    Parses the menu for 'Olive' restaurant.
    """
    start_index = html.find('id="dennimenu"')
    end_index = html.find('recenze-link">sem<') # Marker for the end of the menu section

    if start_index == -1 or end_index == -1:
        return [] # Menu section not found

    text = html[start_index:end_index]
    # Find all div elements with class "dm-jidlo"
    raw_list = re.findall(r'<div class="dm-jidlo">(.*?)</div>', text)
    grouped = []
    # Items are typically grouped in sets of 3 (name, price part 1, price part 2)
    for i in range(0, len(raw_list), 3):
        try:
            name_raw = raw_list[i]
            price_raw = raw_list[i+1] + ' ' + raw_list[i+2] # Combine price parts
            name = name_raw.strip()
            price = price_raw.strip()
            if name and "Kč" in price:
                grouped.append({'name': name, 'price': price})
        except IndexError:
            # Handle cases where the list might not be perfectly divisible by 3 at the end
            continue
    return grouped

def parse_menu_theta(html):
    """
    Parses the menu for 'Pub' restaurant based on the current day.
    """
    today = datetime.today().strftime('%A') # e.g., 'Monday'

    # The start ID is often the same for all days for The Pub
    day_start_ids = {
        'Monday': 'menu-poledni-menu-content',
        'Tuesday': 'menu-poledni-menu-content',
        'Wednesday': 'menu-poledni-menu-content',
        'Thursday': 'menu-poledni-menu-content',
        'Friday': 'menu-poledni-menu-content'
    }
    # End markers are the headings for the next day's menu or a permanent menu section
    day_end_markers = {
        'Monday': '<h3 class="font-heading uppercase text-3xl font-bold">úterý',
        'Tuesday': '<h3 class="font-heading uppercase text-3xl font-bold">středa',
        'Wednesday': '<h3 class="font-heading uppercase text-3xl font-bold">čtvrtek',
        'Thursday': '<h3 class="font-heading uppercase text-3xl font-bold">pátek',
        'Friday': 'menu-poledni-menu-perm-content' # End of Friday's menu is the start of permanent menu
    }

    start_id = day_start_ids.get(today)
    end_marker = day_end_markers.get(today)

    if not start_id:
        return []

    start_index = html.find(f'id="{start_id}"')
    
    if start_index == -1:
        return []

    end_index = html.find(end_marker)

    # Special handling for Friday or if the end marker isn't found
    if today == 'Friday' and end_index == -1:
        # If Friday's end marker isn't found, try to find a more general end
        end_index = html.find('menu-poledni-menu-perm-content') # Fallback for Friday

    # Ensure valid slice range
    if start_index >= end_index or end_index == -1: # If end_index is before start_index or not found effectively
        text = html[start_index:] # Take from start to end of document
    else:
        text = html[start_index:end_index]

    # Regex to find item names (strong tags) and prices (span tags)
    pattern = re.compile(r'<strong[^>]*>(.*?)<\/strong>.*?<span[^>]*>(\d+)\s*&nbsp;Kč<\/span>', re.DOTALL)
    matches = pattern.findall(text)
    cleaned_items = []
    for name, price in matches:
        cleaned_items.append({'name': name.strip(), 'price': price.strip() + ' Kč'}) # Add Kč back for consistency
    return cleaned_items

def load_menu(restaurant):
    """
    Fetches the menu from a given restaurant URL and parses it.
    """
    try:
        resp = requests.get(restaurant['url'], timeout=10)
        resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # *** CRITICAL FIX FOR UNICODEDECODEERROR ***
        # Explicitly set the encoding to UTF-8.
        # This tells requests to interpret the raw bytes of the response as UTF-8.
        resp.encoding = 'utf-8'

        parser_func = globals()[restaurant["parser"]] # Get the parser function by name
        items = parser_func(resp.text) # Pass the explicitly decoded text to the parser
        return {"name": restaurant["name"], "items": items}
    except requests.exceptions.RequestException as e:
        # Catch specific requests exceptions for network errors, timeouts, etc.
        print(f"Network or HTTP error fetching menu for {restaurant['name']}: {e}")
        return {"name": restaurant["name"], "items": [f"(Network Error: {e})"]}
    except Exception as e:
        # Catch any other parsing or unexpected errors
        print(f"General error fetching or parsing menu for {restaurant['name']}: {e}")
        return {"name": restaurant["name"], "items": [f"(Error fetching menu: {e})"]}

def generate_poll_html(question, options):
    """
    Generates HTML for a poll based on restaurant names.
    """
    # Extract just the names from the menu options
    opt = [item['name'] for item in options if 'name' in item]
    opt.append("Nakupak") # Add a custom option
    
    html = f"<form class='sticky-poll' method='post' action='/vote'>\n"
    html += f"<h3>{question}</h3>\n"
    for option in opt:
        # Ensure option is HTML-safe if it contains user-controlled input
        # For this case, it's restaurant names, so less critical, but good practice.
        html += f"<button type='submit' name='poll' value='{option}'>{option}</button>\n"
    html += "</form>"
    return html

def render_html(menu_data):
    """
    Renders the HTML template with the fetched menu data and poll.
    """
    # Set up Jinja2 environment to load templates from the script's directory
    env = Environment(loader=FileSystemLoader(script_dir))
    template = env.get_template(TEMPLATE_FILE) # Load the template file
    
    # Generate the poll HTML
    poll_html = generate_poll_html("Where do we go for lunch?", menu_data)
    
    # Render the template with dynamic data
    # Pass an empty dictionary for vote_counts when rendering from scrape.py
    # This prevents the 'UndefinedError' because scrape.py doesn't have vote data.
    output = template.render(
        date=datetime.today().strftime("%A, %d.%m.%Y"), # Current date
        menus=menu_data, # List of restaurant menus
        poll=poll_html, # The generated poll HTML
        vote_counts={} # Provide an empty dict for vote_counts
    )
    
    # Create the output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Write the rendered HTML to an index.html file in the output directory
    # Explicitly specify UTF-8 encoding for writing
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding='utf-8') as f:
        f.write(output)

def main():
    """
    Main function to load menus, render HTML, and print status.
    """
    print("Loading menus...")
    menus = [load_menu(r) for r in RESTAURANTS] # Fetch menus for all restaurants
    render_html(menus) # Generate the HTML output
    print("✓ Menu summary generated: output/index.html")

if __name__ == "__main__":
    main()
