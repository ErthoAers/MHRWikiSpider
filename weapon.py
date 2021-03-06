import requests
import re
import os
from bs4 import BeautifulSoup
import urllib.parse
import json
import multiprocessing.pool
from utils import *

with open("json/item_id.json", encoding='utf-8') as f:
    item_id = json.load(f)

with open("json/rampage_skill.json", encoding="utf-8") as f:
    rampage_skills_dict = json.load(f)
rampage_skills_dict = {i["name"]: i["id"] for i in rampage_skills_dict}

with open("json/melody.json", encoding="utf-8") as f:
    melody_dict = json.load(f)
melody_dict = {i["name"]: i["id"] for i in melody_dict}

def fetch_stat(stat, w):
    stat = stat.find_all(class_="mh-kv")
    
    slot_expr = r"^/resources/slot_(\d).png$"
    raw_slot = stat[3].contents[1].find_all(src=re.compile(slot_expr))
    slot = [0, 0, 0]
    for s in range(len(raw_slot)):
        if raw_slot[s]["src"] == "":
            continue
        slot[s] = int(re.match(slot_expr, raw_slot[s]["src"]).group(1)) + 1
    
    stat_entry = {
        "attack": int(stat[0].contents[1].text),
        "affinity": int(stat[1].contents[1].text[:-1]),
        "defense": int(stat[2].contents[1].text),
        "slot": slot
    }

    if w not in ["LightBowgun", "HeavyBowgun"]:
        raw_element = stat[4].contents[1].text.split()
        element = {"name": camel_to_snake(raw_element[0]), "value": int(raw_element[1])}
        stat_entry["element"] = element

    if w not in ["LightBowgun", "HeavyBowgun", "Bow"]:
        raw_sharpness = stat[5].contents[1].find_all(class_="mh-sharpness")
        raw_sharpness_half = stat[5].contents[1].find_all(class_="mh-sharpness-half")
        sharpness = [float(re.match(r"^width:([\d\.]+)\%\;$", i["style"]).group(1)) for i in raw_sharpness]
        sharpness_half = [0.0] * 7
        for s in raw_sharpness_half:
            index = int(s["class"][0][-1])
            if index >= 7:
                continue
            sharpness_half[index] = float(float(re.match(r"^width:([\d\.]+)\%\;$", s["style"]).group(1)))
        stat_entry["sharpness"] = sharpness
        stat_entry["sharpness_half"] = sharpness_half

    if w == "GunLance":
        raw_type = stat[6].contents[-1]
        type_, level = raw_type.text.split()
        stat_entry["type"] = {
            "name": camel_to_snake(type_),
            "value": int(level)
        }
    
    if w == "SlashAxe":
        raw_bottle = stat[6].contents[-1]
        bottle, value = raw_bottle.text.split()
        stat_entry["bottle"] = {
            "name": camel_to_snake(bottle),
            "value": int(value)
        }
    
    if w == "ChargeAxe":
        bottle = stat[6].contents[-1].text
        stat_entry["bottle"] = {
            "name": camel_to_snake(bottle),
            "value": 0
        }
    
    if w == "InsectGlaive":
        stat_entry["insect_level"] = int(stat[6].contents[-1].text)
    
    if w == "LightBowgun" or w == "HeavyBowgun":
        stat_entry.update({
            "fluctuation": camel_to_snake(stat[4].contents[-1].text),
            "reload": int(stat[5].contents[-1].text),
            "recoil": int(stat[6].contents[-1].text),
            "kakusan_type": camel_to_snake(stat[7].contents[-1].text)
        })
    
    if w == "HeavyBowgun":
        stat_entry["unique_bullet"] = camel_to_snake(stat[8].contents[-1].text)
    
    if w == "Bow":
        raw_charge_type = stat[6].contents[-1].text.split("-")
        tmp = [camel_to_snake(i).split("_") for i in raw_charge_type if i != "None"]
        charge_type = [{"name": "_".join(i[:-1]), "level": int(i[-1][-1])} for i in tmp]

        stat_entry.update({
            "default_charge_level": int(stat[5].contents[-1].text),
            "charge_type": charge_type,
            "curve_type": int(stat[7].contents[-1].text)
        })

    return stat_entry

def fetch_rampage_skills(rampage_skills):
    raw_rampage_skill = rampage_skills.find_all(class_=en_tag)
    rampage_skills_entry = []
    str_expr = re.compile(r"[\:\(\)]")
    for skill in raw_rampage_skill:
        text = skill.text.split()
        key = "_".join(str_expr.sub("", i.lower()).replace("-", "_") for i in text)
        rampage_skills_entry.append(rampage_skills_dict[key])

    return rampage_skills_entry

def fetch_melody(melody):
    raw_melody = melody.find_all(class_=en_tag)
    melody_entry = []
    str_expr = re.compile(r"[\:\(\)\+]")
    for m in raw_melody:
        text = [str_expr.sub("", i.lower()).replace("-", "_") for i in m.text.split()]
        text = [i for i in text if i != ""]
        key = "_".join(text)
        melody_entry.append(melody_dict[key])
    
    return melody_entry

def fetch_ammo_list(ammo_list):
    raw_ammo_list = ammo_list.find("tbody").find_all("tr")
    ammo_entry = []
    for ammo in raw_ammo_list:
        try:
            ammo["class"]
        except:
            if ammo.text.startswith("<"):
                continue
            contents = ammo.contents
            shot_type = [i.strip().lower().replace(" ", "_") for i in contents[2].text.split(",")]
            ammo_type = contents[0].text.lower().replace(" ", "_")
            if ammo_type == "amor_ammo":
                ammo_type = "armor_ammo"
            if ammo_type == "piercing_drago_ammo":
                ammo_type = "piercing_dragon_ammo"
            ammo_entry.append({
                "ammo_type": ammo_type,
                "capacity": int(contents[1].text),
                "shot_type": shot_type if shot_type[0] != "" else []
            })

    return ammo_entry

def fetch_bottle(bottle):
    raw_bottle = bottle.find_all("li")
    bottles = [i.text.lower().replace(" ", "_") for i in raw_bottle]
    for i, bottle in enumerate(bottles):
        if bottle.endswith("power_up"):
            bottles[i] = f"{bottle[:-8]}_power_up"
    return bottles

def fetch_crafting(crafting, w):
    crafting = crafting.find("tbody").contents
    crafting_entry = []

    for c in crafting:
        contents = c.contents
        entry = {}
    
        method = contents[0].text.split()[0].lower()
        if method == "as":
            method = "as_layered"
        entry["method"] = method
        entry["basic"] = -1
        if method == "upgrade":
            basic = weapon_id[w][contents[0].find(class_=en_tag).text]
            entry["basic"] = basic

        categorized_material = {"material": "none", "point": 0}
        if contents[1].text != "-":
            material, point = contents[1].contents
            categorized_material["material"] = material.find(class_=en_tag).text
            categorized_material["point"] = int(point.split()[0])
        entry["categorized_material"] = categorized_material

        raw_material = contents[2].find_all("li")
        material = []
        for m in raw_material:
            num = int(re.match(r"^(\d+)x$", m.text.split()[0]).group(1))
            id_ = item_id[m.find(class_=en_tag).text]
            material.append({
                "id": id_,
                "num": num
            })
        entry["material"] = material

        raw_output = contents[3].find_all("li")
        output = []
        for o in raw_output:
            num = int(re.match(r"^(\d+)x$", o.text.split()[0]).group(1))
            id_ = item_id[o.find(class_=en_tag).text]
            output.append({
                "id": id_,
                "num": num
            })
        entry["output"] = output

        crafting_entry.append(entry)

    return crafting_entry

def fetch_upgrade(upgrade, w):
    raw_upgrade = upgrade.find_all("li")
    upgrade_entry = []
    for u in raw_upgrade:
        upgrade_entry.append(weapon_id[w][u.find(class_=en_tag).text])
    return upgrade_entry

def fetch(link):
    rarity = int(link.find("div").find("div")["class"][0].split("-")[-1])
    link = link["href"]
    
    weaponURL = urllib.parse.urljoin(baseURL, link)

    r = requests.get(weaponURL)
    r.encoding = "utf-8"        
    soup = BeautifulSoup(r.text, features="lxml")

    title = soup.find(class_="title")
    name = "".join(title.find(class_=en_tag).text.split())
    name = camel_to_snake(name).replace("'", "_")

    expr = r"^/weapon/([A-Za-z]+)_(\d{3}).html$"
    match = re.match(expr, link)
    w = match.group(1)
    id_ = weapon_id[camel_to_snake(w)][title.find(class_=en_tag).text]
    if name == "flammenschild" and rarity == 3:
        id_ -= 1
    print(w, id_)

    section = soup.find_all("section")
    description = section[0]
    stat = section[1]
    rampage_skills = section[2]
    if w not in ["Horn", "LightBowgun", "HeavyBowgun", "Bow"]:
        crafting = section[3]
        upgrade = section[4]
    else:
        crafting = section[4]
        upgrade = section[5]

    stat_entry = fetch_stat(stat, w)
    rampage_skills_entry = fetch_rampage_skills(rampage_skills)
    crafting_entry = fetch_crafting(crafting, camel_to_snake(w))
    upgrade_entry = fetch_upgrade(upgrade, camel_to_snake(w))

    entry = {
        "id": id_,
        "rarity": rarity,
        "genre": camel_to_snake(w),
        "name": name,
        "name_entry": [{
            "text": title.find(class_=en_tag).text,
            "language": "en"
        }],
        "description_entry": [{
            "text": description.find(class_=en_tag).text.replace("\r\n", " ").replace("- ", ""),
            "language": "en"
        }]
    }
    entry.update(stat_entry)
    entry["rampage_skills"] = rampage_skills_entry

    if w == "Horn":
        melody = section[3]
        entry["melody"] = fetch_melody(melody)

    if w == "LightBowgun" or w == "HeavyBowgun":
        ammo_list = section[3]
        entry["ammo_list"] = fetch_ammo_list(ammo_list)

    if w == "Bow":
        bottle = section[3]
        entry["bottle"] = fetch_bottle(bottle)

    entry["crafting"] = crafting_entry
    entry["upgrade"] = upgrade_entry

    for lang, lang_tag in languages[1:]:
        lang_tag = f"mh-lang-{lang_tag}"

        entry["name_entry"].append({
            "text": title.find(class_=lang_tag).text,
            "language": lang
        })

        entry["description_entry"].append({
            "text": description.find(class_=lang_tag).text.replace("\r\n", "" if lang in ["ja", "zh", "zh-Hant"] else " ").replace("- ", ""),
            "language": lang
        })
    
    return entry

links = {}
weapon = {}
os.makedirs("json/weapon", exist_ok=True)
for w in weapon_list:
    # print(w)
    os.makedirs(f"img/weapon/{w}", exist_ok=True)
    weaponListURL = urllib.parse.urljoin(baseURL, f"weapon/{w}.html")
    r = requests.get(weaponListURL)
    r.encoding = "utf-8"

    expr = f"/weapon/{''.join(i.capitalize() for i in w.split('_'))}" + r"_(\d{3}).html"
    soup = BeautifulSoup(r.text, features="lxml")
    links[w] = [i for i in soup.find_all(href=re.compile(expr))]

    weapon_id_URL = f"https://mhrise.kiranico.com/data/weapons?scope=wp&value={weapon_list[w]}"
    r = requests.get(weapon_id_URL)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, features="lxml")
    weapon_items = soup.find("tbody").find_all(class_="bg-white")
    if os.path.exists("json/weapon_id.json"):
        with open("json/weapon_id.json", encoding="utf-8") as f:
            weapon_id = json.load(f)
    else:
        weapon_id[w] = {}
        for weapon_item in weapon_items:
            weapon_info = weapon_item.find("a")
            name = weapon_info.text
            img_id = re.match(r"https://mhrise.kiranico.com/data/weapons/(\d+)", weapon_info["href"]).group(1)
            
            r_w = requests.get(weapon_info["href"])
            s_w = BeautifulSoup(r_w.text, features="lxml")

            weapon_id[w][name] = int(s_w.find(class_="sm:grid-cols-4").find(class_="sm:col-span-1").find("dd").text.strip())
            img = requests.get(f"https://cdn.kiranico.net/file/kiranico/mhrise-web/images/rotate/{img_id}.png")
            with open(f"img/weapon/{w}/{w}_{weapon_id[w][name]}.png", "wb") as f:
                f.write(img.content)
            print(f"{w} {weapon_id[w][name]} saved.")

with open("json/weapon_id.json", "w", encoding="utf-8") as f:
    json.dump(weapon_id, f)

for w in weapon_list:
    weapon[w] = []
    pool = multiprocessing.pool.ThreadPool(16)
    pool.map(lambda x: weapon[w].append(fetch(x)), links[w])
    weapon[w].sort(key=lambda x: x["id"])

    with open(f"json/weapon/{w}.json", "w", encoding="utf-8") as f:
        json.dump(weapon[w], f, indent=4, ensure_ascii=False)
