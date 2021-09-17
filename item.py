import requests
import re
import os
from bs4 import BeautifulSoup
import urllib.parse
import json
import multiprocessing.pool
from utils import *

def fetch_icon(icon):
    icon_div = icon.find_all("div")
    color = int(icon_div[0]["class"][0].split("-")[-1])
    icon_expr = r"mask-image: url\('/resources/item/(\d+).r.png'\)"
    icon_id = int(re.match(icon_expr, icon_div[0]["style"]).group(1))

    addon = "none"

    r = requests.get(urllib.parse.urljoin(baseURL, f"/resources/item/{icon_id:03}.r.png"))
    a = requests.get(urllib.parse.urljoin(baseURL, f"/resources/item/{icon_id:03}.a.png"))
    with open(f"img/item/item_{icon_id:03}.r.png", "wb") as f:
        f.write(r.content)
    with open(f"img/item/item_{icon_id:03}.a.png", "wb") as f:
        f.write(a.content)

    if icon_div[2].find("div") != None:
        addon = icon_div[-1]["class"][0].split("-")[-1]
    
    return {
        "id": icon_id,
        "color": color,
        "addon": addon
    }

def fetch(link):
    expr = r"/item/normal_(\d+).html"
    itemURL = urllib.parse.urljoin(baseURL, link)
    
    r = requests.get(itemURL)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, features="lxml")

    title = soup.find(class_="title")
    description, basic_data = soup.find_all("section")
    icon = soup.find(class_="mh-colored-icon")
    data = basic_data.find_all(class_="mh-kv")
    name = "_".join(i.lower() for i in title.find(class_=en_tag).text.strip().split())

    if name.startswith("#reject") or name == "":
        return

    id_ = item_id[title.find(class_=en_tag).text.strip()]
    icon_entry = fetch_icon(icon)

    if id_ == 10000:
        return

    material = {}
    print(id_)
    c = data[12].contents[1].contents
    if len(c) == 1:
        material["material"] = ""
        material["point"] = 0
    else:
        material["material"] = " ".join(i.find(class_=en_tag).text.strip() for i in c[:-1])
        material["point"] = int(c[-1].split()[0])

    entry = {
        "id": id_,
        "name": name,
        "icon": icon_entry,
        "carriable_filter": data[0].contents[1].text.lower(),
        "type": camel_to_snake(data[1].contents[1].text.strip()),
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
        "evaluation_value": int(data[13].contents[1].text),
        "crafting": item_crafting.setdefault(id_, [])
    }

    entry["name_entry"] = [{
        "text": title.find(class_=en_tag).text.strip(),
        "language": "en"
    }]

    entry["description_entry"] = [{
        "text": description.find(class_=en_tag).text.strip(),
        "language": "en"
    }]
    
    for lang, lang_tag in languages[1:]:
        lang_tag = f"mh-lang-{lang_tag}"

        entry["name_entry"].append({
            "text": title.find(class_=lang_tag).text.strip(),
            "language": lang
        })

        entry["description_entry"].append({
            "text": description.find(class_=lang_tag).text.strip(),
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

if os.path.exists("json/item_id.json"):
    with open("json/item_id.json") as f:
        item_id = json.load(f)
else:
    r = requests.get("https://mhrise.kiranico.com/data/items")
    soup = BeautifulSoup(r.text, features="lxml")
    tab = [0, 1, 2, 3, 4, 5, 7, 8, 11]
    item_trs = []
    for i in tab:
        item_trs += soup.find(attrs={"x-show": f"tab === 'type{i}'"}).find("tbody").find_all("tr")

    for item_tr in item_trs:
        name = item_tr.find("a").text
        r = requests.get(item_tr.find("a")["href"])
        soup = BeautifulSoup(r.text, features="lxml")
        item_id[name] = int(soup.find(class_="sm:grid-cols-4").find_all(class_="sm:col-span-1")[4].find("dd").text)
        print(f"{name} {item_id[name]} saved.")
    
    item_id.update({"Bishaten Talon": 646, "Massive Bone": 455})
    with open("json/item_id.json", "w") as f:
        json.dump(item_id, f)

if os.path.exists("json/item_crafting.json"):
    with open("json/item_crafting.json") as f:
        item_crafting = json.load(f)
else:
    r = requests.get("https://mhrise.kiranico.com/data/item-mix-recipes")
    soup = BeautifulSoup(r.text, features="lxml")
    crafting_trs = soup.find("tbody").find_all("tr")
    for crafring_tr in crafting_trs:
        material = crafring_tr.find_all("td")
        output = item_id[material[1].text]
        item_crafting[output] = item_crafting.setdefault(output, [])
        item_crafting[output].append([item_id[material[2].text]])
        if material[3].text != "":
            item_crafting[output][-1].append(item_id[material[3].text])

    with open("json/item_crafting.json", "w") as f:
        json.dump(item_crafting, f)

os.makedirs("img/item", exist_ok=True)
pool = multiprocessing.pool.ThreadPool(16)
pool.map(lambda x: item.append(fetch(x)), links)

item = [i for i in item if i != None]
item.sort(key=lambda x: x["id"])

with open("json/item.json", "w", encoding="utf-8") as f:
    json.dump(item, f, indent=4, ensure_ascii=False)
