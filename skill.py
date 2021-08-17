import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
import json
import multiprocessing.pool
from utils import *

def fetch_level(level):
    raw_level = level.find_all("li")
    level_entry = []
    for l in raw_level:
        description_entry = []
        for lang, lang_tag in languages:
            lang_tag = f"mh-lang-{lang_tag}"
            description_entry.append({
                "text": l.find(class_=lang_tag).text,
                "language": lang
            })
        level_entry.append(description_entry)
    return level_entry

def fetch_decoration(decoration):
    raw_decoration = decoration.find("tbody").find_all("td")
    name_list = raw_decoration[0].find(class_=en_tag).text.split()
    name = "".join(name_list[:-1])
    name = camel_to_snake(name) + f"_{name_list[-1]}"

    decoration_entry = {
        "name": name,
        "name_entry": [{
            "text": raw_decoration[0].find(class_=en_tag).text,
            "language": "en"
        }],
        "slot": int(name_list[-1]),
    }

    for lang, lang_tag in languages[1:]:
        lang_tag = f"mh-lang-{lang_tag}"
        decoration_entry["name_entry"].append({
            "text": raw_decoration[0].find(class_=lang_tag).text,
            "language": lang
        })

    raw_material = raw_decoration[1].find_all("li")
    material = []
    for m in raw_material:
        item_expr = r"/item/normal_(\d+).html"
        num = int(re.match(r"^(\d+)x$", m.text.split()[0]).group(1))
        id_ = int(re.match(item_expr, m.find(href=re.compile(item_expr))["href"]).group(1))
        material.append({
            "id": id_,
            "num": num
        })

    decoration_entry["material"] = material

    return decoration_entry

def fetch(link):
    expr = r"^/skill/(\d{3}).html$"
    match = re.match(expr, link)
    skill_id = int(match.group(1))
    print(skill_id)
    skillURL = urllib.parse.urljoin(baseURL, link)

    r = requests.get(skillURL)
    r.encoding = "utf-8"        
    soup = BeautifulSoup(r.text, features="lxml")

    title = soup.find(class_="title")
    name = "".join(title.find(class_=en_tag).text.split())
    name = camel_to_snake(name).replace("'", "_")
    description = title.find_next_sibling("div")
    level = soup.find("ul")
    decoration = soup.find("section")

    level_entry = fetch_level(level)

    entry = {
        "id": skill_id,
        "name": name,
        "name_entry": [{
            "text": title.find(class_=en_tag).text,
            "language": "en"
        }],
        "description_entry": [{
            "text": description.find(class_=en_tag).text,
            "language": "en"
        }],
        "max_level": len(level_entry),
        "level": level_entry
    }
    if decoration != None:
        entry["decoration"] = fetch_decoration(decoration)

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

skillListURL = urllib.parse.urljoin(baseURL, "skill.html")
r = requests.get(skillListURL)
r.encoding = "utf-8"

expr = r"^/skill/(\d{3}).html$"
soup = BeautifulSoup(r.text, features="lxml")
links = [i["href"] for i in soup.find_all(href=re.compile(expr))]
skill = []

pool = multiprocessing.pool.ThreadPool(16)
pool.map(lambda x: skill.append(fetch(x)), links)

skill.sort(key=lambda x: x["id"])

with open("json/skill.json", "w", encoding="utf-8") as f:
    json.dump(skill, f)
