import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
import json
import multiprocessing.pool
from utils import *

def fetch_basic_data(basic_data):
    raw_basic_data = basic_data.find_all("p")
    hp_expr = r"^Base HP: (\d+)$"
    limping_expr = r"^Limping threshold: \(village\) (\d+)% / \(LR\) (\d+)% / \(HR\) (\d+)%$"
    capturing_expr = r"^Capturing threshold: \(village\) (\d+)% / \(LR\) (\d+)% / \(HR\) (\d+)%$"
    sleep_expr = r"^Sleep recovering: (\d+) seconds / recover (\d+)% HP$"
    
    limping_match = re.match(limping_expr, raw_basic_data[1].text)
    capturing_match = re.match(capturing_expr, raw_basic_data[2].text)
    sleep_match = re.match(sleep_expr, raw_basic_data[3].text)
    entry = {
        "hp": int(re.match(hp_expr, raw_basic_data[0].text).group(1)),
        "limping_threshold": {
            "village": int(limping_match.group(1)),
            "low_rank": int(limping_match.group(2)),
            "high_rank": int(limping_match.group(3))
        },
        "capturing_threshold": {
            "village": int(capturing_match.group(1)),
            "low_rank": int(capturing_match.group(2)),
            "high_rank": int(capturing_match.group(3))
        },
        "sleep_recovering": {
            "time": int(sleep_match.group(1)),
            "recovering": int(sleep_match.group(2))
        }
    }

    return entry

def fetch_quests(quests):
    raw_quests = quests.find("tbody").find_all("tr")
    quests_entry = []
    quest_expr = r"^/quest/(\d{6}).html$"
    for quest in raw_quests:
        quest_info = quest.find_all("td")
        name = quest_info[0]
        if name.text == "Village tour":
            id_ = 1
        elif name.text == "Low rank tour":
            id_ = 2
        elif name.text == "High rank tour":
            id_ = 3
        else:
            id_ = int(re.match(quest_expr, quest_info[0].find("a")["href"]).group(1))
        size = quest_info[1].find_all(class_="tag")
        small_crown = king_crown = 0
        if len(size) != 0:
            for s in size:
                crown = s.find("img")["src"]
                if crown == "/resources/small_crown.png":
                    small_crown = int(s.text[:-1])
                else:
                    king_crown = int(s.text[:-1])

        quests_entry.append({
            "id": id_,
            "small_crown": small_crown,
            "king_crown": king_crown,
            "hp_rate": float(quest_info[2].text[1:]),
            "attack_rate": float(quest_info[3].text[1:]),
            "parts_rate": float(quest_info[4].text[1:]),
            "defense_rate": float(quest_info[5].text[1:]),
            "ailment_rate": float(quest_info[6].text[1:]),
            "stun_rate": float(quest_info[8].text[1:]),
            "exhaust_rate": float(quest_info[9].text[1:]),
            "ride_rate": float(quest_info[10].text[1:]),
            "stamina": float(quest_info[11].text)
        })
    return quests_entry

def fetch_hitzone_data(hitzone_data, id_, subid):
    imageURL = urllib.parse.urljoin(baseURL, hitzone_data.find("img")["src"])
    image = requests.get(imageURL)
    with open(f"img/monster/{id_:03}_{subid:02}_meat.png", "wb") as f:
        f.write(image.content)
    raw_hitzone = hitzone_data.find("tbody").find_all("tr")
    invalid = len(hitzone_data.find("tbody").find_all(class_="mh-invalid-meat"))
    hitzone_entry = []
    
    index = 0
    while index < len(raw_hitzone) - invalid:
        first_line = raw_hitzone[index].find_all("td")
        phase = int(first_line[0]["rowspan"])
        name = "".join(first_line[2].find(class_=en_tag).text.split())
        name = camel_to_snake(name)

        hitzone_phase = {
            "phase": phase,
            "name": name,
        }
        hitzone_phase["name_entry"] = [{
            "text": first_line[2].find(class_=en_tag).text,
            "language": "en"
        }]
        for lang, lang_tag in languages[1:]:
            lang_tag = f"mh-lang-{lang_tag}"

            hitzone_phase["name_entry"].append({
                "text": first_line[2].find(class_=lang_tag).text,
                "language": lang
            })
        hitzone_phase["info"] = []

        for i in range(phase):
            hitzone_info = raw_hitzone[i + index].find_all("td")
            if i == 0:
                hitzone_info = hitzone_info[1:]
            hitzone_phase["info"].append({
                "slash": int(hitzone_info[2].text),
                "impact": int(hitzone_info[3].text),
                "shot": int(hitzone_info[4].text),
                "fire": int(hitzone_info[5].text),
                "water": int(hitzone_info[6].text),
                "ice": int(hitzone_info[7].text),
                "thunder": int(hitzone_info[8].text),
                "dragon": int(hitzone_info[9].text),
                "stun": int(hitzone_info[10].text)
            })
        hitzone_entry.append(hitzone_phase)
        index += phase
    return hitzone_entry

# def fetch_parts(parts, id_, subid, hitzone_entry):
#     imageURL = urllib.parse.urljoin(baseURL, parts.find("img")["src"])
#     image = requests.get(imageURL)
#     with open(f"img/monster/{id_:03}_{subid:02}_parts.png", "wb") as f:
#         f.write(image.content)
    
#     name_entry = {}
#     for hitzone in hitzone_entry:
#         name_entry[hitzone["name_entry"][1]["text"]] = hitzone["name_entry"]

#     raw_parts = parts.find("tbody").find_all("tr")
#     invalid = len(parts.find("tbody").find_all(class_="mh-invalid-part"))
#     part_entry = []
#     for i in range(len(raw_parts) - invalid):
#         part_info = raw_parts[i].find_all("td")
#         part_name_entry = name_entry[part_info[0].text.split()[-1]]
#         part_name = part_name_entry[0]["text"]
#         stagger = int(part_info[1].text)
#         break_match = re.match(r"\(x(\d)\) (\d+)", part_info[2])

def fetch_abnormal_status(abnormal_status):
    raw_abnormal_status = [i for i in abnormal_status.find("tbody").find_all("tr") 
                           if "mh-no-preset" not in i.get_attribute_list("class")]
    for abnormal in raw_abnormal_status:
        abnormal_info = abnormal.find_all("td")
        name = camel_to_snake("".join(i.capitalize() for i in abnormal_info[0].text.split()))
        threshold = re.match(r"^(\d+) \(\+(\d+)\) → (\d+)$", abnormal_info[1].find(class_="mh-default-cond").text)
        decay = re.match(r"(\d+) / (\d+) sec", abnormal_info[2].find(class_="mh-default-cond").text)
        max_stock = int(abnormal_info[3].text)
        active_time = re.match(r"(\d+) sec \(-(\d+) sec\) → (\d+) sec", abnormal_info[4].text)
        add_tired_time = re.match(r"\+(\d+) sec", abnormal_info[5].text)
        damage = re.match(r"(\d+) / (\d+) sec", abnormal_info[6].text)
        


def fetch(link):
    expr = r"^/monster/(\d{3})_(\d{2}).html$"
    match = re.match(expr, link)
    monster_id = int(match.group(1))
    monster_subid = int(match.group(2))
    monsterURL = urllib.parse.urljoin(baseURL, link)

    print(monster_id, monster_subid)
    r = requests.get(monsterURL)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, features="lxml")

    imageURL = urllib.parse.urljoin(baseURL, soup.find(class_="mh-monster-header").find("img")["src"])
    image = requests.get(imageURL)
    with open(f"img/monster/{monster_id:03}_{monster_subid:02}_icon.png", "wb") as f:
        f.write(image.content)

    title = soup.find(class_="title")
    name = "".join(title.find(class_=en_tag).text.replace("-", " ").split())
    name = camel_to_snake(name)

    section = soup.find_all("section")
    basic_data = section[0]
    quests = section[1]
    hitzone_data = section[2]
    parts = section[3]
    abnormal_status = section[4]
    low_rank_reward = section[5]
    high_rank_reward = section[6]

    

links = []
monsterListURL = urllib.parse.urljoin(baseURL, "monster.html")
r = requests.get(monsterListURL)
r.encoding = "utf-8"

expr = r"^/monster/(\d{3})_(\d{2}).html$"
soup = BeautifulSoup(r.text, features="lxml")
links = [i["href"] for i in soup.find_all(href=re.compile(expr))]
monster = []
