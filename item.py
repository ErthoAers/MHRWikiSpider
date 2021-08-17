import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
import json
import multiprocessing.pool
from utils import *

baseURL = "http://mhrise.mhrice.info"

languages = [
    ("en", 1),
    ("ja", 0),
    ("fr", 2),
    ("it", 3),
    ("de", 4),
    ("es", 5),
    ("ru", 6),
    ("pl", 7),
    ("ko", 11),
    ("zh-Hant", 12),
    ("zh", 13)
]

def fetch(link):
    expr = r"/item/normal_(\d+).html"
    item_id = int(re.match(expr, link).group(1))
    itemURL = urllib.parse.urljoin(baseURL, link)
    
    r = requests.get(itemURL)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, features="lxml")

    title = soup.find(class_="title")
    description, basic_data = soup.find_all("section")
    data = basic_data.find_all(class_="mh-kv")
    name = "_".join(i.lower() for i in title.find(class_=en_tag).text.split())

    if name.startswith("#Reject"):
        return
    
    material = {}
    print(item_id)
    c = data[12].contents[1].contents
    if len(c) == 1:
        material["material"] = ""
        material["point"] = 0
    else:
        material["material"] = " ".join(i.find(class_=en_tag).text for i in c[:-1])
        material["point"] = int(c[-1].split()[0])

    entry = {
        "id": item_id,
        "name": name,
        "carriable_filter": data[0].contents[1].text.lower(),
        "type": camel_to_snake(data[1].contents[1].text),
        "rarity": int(data[2].contents[1].text),
        "maximum_carry": int(data[3].contents[1].text),
        "maximum_carry_by_buddy": int(data[4].contents[1].text),
        "in_item_bar": True if data[5].contents[1].text == "true" else False,
        "in_action_bar": True if data[6].contents[1].text == "true" else False,
        "infinite": True if data[7].contents[1].text == "true" else False,
        "fixed_item": True if data[8].contents[1].text == "true" else False,
        "sell_price": int(data[9].contents[1].text),
        "buy_price": int(data[10].contents[1].text),
        "item_group": data[11].contents[1].text.lower(),
        "material_category": material,
        "evaluation_value": int(data[13].contents[1].text)
    }

    entry["name_entry"] = [{
        "text": title.find(class_=en_tag).text,
        "language": "en"
    }]

    entry["description_entry"] = [{
        "text": description.find(class_=en_tag).text,
        "language": "en"
    }]
    
    for lang, lang_tag in languages[1:]:
        lang_tag = f"mh-lang-{lang_tag}"

        entry["name_entry"].append({
            "text": title.find(class_=lang_tag).text,
            "language": lang
        })

        entry["description_entry"].append({
            "text": description.find(class_=lang_tag).text,
            "language": lang
        })
    
    return entry

itemListURL = urllib.parse.urljoin(baseURL, "item.html")
r = requests.get(itemListURL)
r.encoding = "utf-8"

expr = r"/item/normal_(\d+).html"
soup = BeautifulSoup(r.text, features="lxml")
links = [i["href"] for i in soup.find_all(href=re.compile(expr))]
item = []

pool = multiprocessing.pool.ThreadPool(16)
pool.map(lambda x: item.append(fetch(x)), links)

item.sort(key=lambda x: x["id"])

with open("json/item.json", "w", encoding="utf-8") as f:
    json.dump(item, f)
