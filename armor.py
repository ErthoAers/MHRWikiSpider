import requests
import re
import os
from bs4 import BeautifulSoup
import urllib.parse
import json
import multiprocessing.pool
from utils import *

armor_id = {}

def fetch_stat(stat):
    raw_stat = stat.find("tbody").find_all("tr")
    stat_entry = []

    for a in raw_stat:
        if a.text.strip() == "-":
            stat_entry.append({})
            continue

        armor_stat = a.find_all("td")
        str_expr = re.compile(r"[\.\-\(\)\']")
        title = armor_stat[0]
        name = title.find(class_=en_tag).text
        name_list = str_expr.sub(" ", name).split()
        name = camel_to_snake("".join(i.capitalize() for i in name_list))
        sell_price, buy_price = (int(i.strip()) for i in armor_stat[1].text.split("/"))
        
        slot_expr = r"^/resources/slot_(\d).png$"
        raw_slot = armor_stat[8].find_all(src=re.compile(slot_expr))
        slot = [0, 0, 0]
        for s in range(len(raw_slot)):
            if raw_slot[s]["src"] == "":
                continue
            slot[s] = int(re.match(slot_expr, raw_slot[s]["src"]).group(1)) + 1
        
        raw_skill = armor_stat[9].find_all("li")
        skill = []
        skill_expr = r"^/skill/(\d{3}).html"
        for s in raw_skill:
            level = int(s.text.split()[-1])
            id_ = int(re.match(skill_expr, s.find(href=re.compile(skill_expr))["href"]).group(1))
            skill.append({
                "id": id_,
                "level": level
            })
        
        armor_stat_entry = {
            "name": name,
            "name_entry": [{
                "text": title.find(class_=en_tag).text,
                "language": "en"
            }],
            "sell_price": sell_price,
            "buy_price": buy_price,
            "defense": int(armor_stat[2].text),
            "resistance": {
                "fire": int(armor_stat[3].text),
                "water": int(armor_stat[4].text),
                "ice": int(armor_stat[5].text),
                "thunder": int(armor_stat[6].text),
                "dragon": int(armor_stat[7].text),
            },
            "slot": slot,
            "skill": skill
        }
        
        for lang, lang_tag in languages[1:]:
            lang_tag = f"mh-lang-{lang_tag}"
            
            armor_stat_entry["name_entry"].append({
                "text": title.find(class_=lang_tag).text,
                "language": lang
            })
        
        stat_entry.append(armor_stat_entry)
    
    return stat_entry

def fetch_crafting(crafting):
    raw_crafting = crafting.find("tbody").find_all("tr")
    crafting_entry = []

    for c in raw_crafting:
        if c.text == "-":
            crafting_entry.append({})
            continue
        
        armor_crafting = c.find_all("td")

        raw_material = armor_crafting[2].find_all("li")
        material = []
        item_expr = r"/item/normal_(\d+).html"
        for m in raw_material:
            num = int(re.match(r"^(\d+)x$", m.text.split()[0]).group(1))
            id_ = int(re.match(item_expr, m.find(href=re.compile(item_expr))["href"]).group(1))
            material.append({
                "id": id_,
                "num": num
            })
        
        raw_output = armor_crafting[3].find_all("li")
        output = []
        item_expr = r"/item/normal_(\d+).html"
        for o in raw_output:
            num = int(re.match(r"^(\d+)x$", o.text.split()[0]).group(1))
            id_ = int(re.match(item_expr, o.find(href=re.compile(item_expr))["href"]).group(1))
            output.append({
                "id": id_,
                "num": num
            })

        armor_crafting_entry = {
            "material": material,
            "output": output
        }
        crafting_entry.append(armor_crafting_entry)
    
    return crafting_entry

def fetch_layered_crafting(layered_crafting):
    raw_layered_crafting = layered_crafting.find("tbody").find_all("tr")
    layered_crafting_entry = []

    for c in raw_layered_crafting:
        if c.text == "-":
            layered_crafting_entry.append({})
            continue

        armor_crafting = c.find_all("td")

        categorized_material = {"material": "none", "point": 0}
        if armor_crafting[1].text != "-":
            material, point = armor_crafting[1].contents
            categorized_material["material"] = material.find(class_=en_tag).text
            categorized_material["point"] = int(point.split()[0])
        
        raw_material = armor_crafting[2].find_all("li")
        material = []
        item_expr = r"/item/normal_(\d+).html"
        for m in raw_material:
            num = int(re.match(r"^(\d+)x$", m.text.split()[0]).group(1))
            id_ = int(re.match(item_expr, m.find(href=re.compile(item_expr))["href"]).group(1))
            material.append({
                "id": id_,
                "num": num
            })
        
        layered_crafting_entry.append({
            "categorized_material": categorized_material,
            "material": material
        })

    return layered_crafting_entry

def fetch(link):
    expr = r"^/armor/(\d{3}).html$"
    id_ = int(re.match(expr, link).group(1))
    armorURL = urllib.parse.urljoin(baseURL, link)

    r = requests.get(armorURL)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, features="lxml")

    title = soup.find(class_="title")
    if title.text == "":
        return None
    
    str_expr = re.compile(r"[\(\)\-]")
    name = "".join(str_expr.sub(" ", title.find(class_=en_tag).text).split())
    name = camel_to_snake(name)

    if id_ not in [64, 65]:
        stat, crafting, layered_crafting = soup.find_all("section")
    else:
        stat, ex_stat, crafting, layered_crafting = soup.find_all("section")
        ex_stat_list = fetch_stat(ex_stat)

    armor_list = fetch_stat(stat)
    crafting_list = fetch_crafting(crafting)
    layered_crafting_list = fetch_layered_crafting(layered_crafting)
    for i in range(len(crafting_list)):
        if id_ in [64, 65]:
            armor_list[i]["ex_skill"] = ex_stat_list[i]["skill"]
        armor_list[i]["crafting"] = crafting_list[i]
        armor_list[i]["layered_crafting"] = layered_crafting_list[i]

    for i in range(5):
        if "name_entry" in armor_list[i]:
            if armor_list[i]["name_entry"][0]["text"] not in armor_id:
                return
            id_ = armor_id[armor_list[i]["name_entry"][0]["text"]]
            break
    print(id_)

    entry = {
        "id": id_,
        "name": name,
        "name_entry": [{
            "title": title.find(class_=en_tag).text,
            "language": "en"
        }],
        "armor_list": armor_list
    }

    for lang, lang_tag in languages[1:]:
        lang_tag = f"mh-lang-{lang_tag}"

        entry["name_entry"].append({
            "text": title.find(class_=lang_tag).text,
            "language": lang
        })
    
    return entry

links = []
armorListURL = urllib.parse.urljoin(baseURL, "armor.html")
r = requests.get(armorListURL)
r.encoding = "utf-8"

expr = r"^/armor/(\d{3}).html$"
soup = BeautifulSoup(r.text, features="lxml")
links = [i["href"] for i in soup.find_all(href=re.compile(expr))]
armor = []

if os.path.exists("json/armor_id.json"):
    with open("json/armor_id.json") as f:
        armor_id = json.load(f)
else:
    r = requests.get("https://mhrise.kiranico.com/data/armors")
    soup = BeautifulSoup(r.text, features="lxml")
    armor_trs = soup.find("tbody").find_all("tr")
    for armor_tr in armor_trs:
        name = armor_tr.find("a").text
        r = requests.get(armor_tr.find("a")["href"])
        soup = BeautifulSoup(r.text, features="lxml")
        armor_id[name] = int(soup.find(class_="sm:grid-cols-4").find_all(class_="sm:col-span-1")[2].find("dd").text)
        print(f"{name} {armor_id[name]} saved.")

    with open("json/armor_id.json", "w") as f:
        json.dump(armor_id, f)

pool = multiprocessing.pool.ThreadPool(16)
pool.map(lambda x: armor.append(fetch(x)), links)
armor = [i for i in armor if i != None]
armor = sorted([i for i in armor if i != None], key=lambda x: x["id"])

with open("json/armor.json", "w", encoding="utf-8") as f:
    json.dump(armor, f, indent=4, ensure_ascii=False)
