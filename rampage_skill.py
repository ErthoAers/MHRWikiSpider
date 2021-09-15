import requests
import re
from bs4 import BeautifulSoup
import urllib.parse
import json

baseURL = "https://mhrise.kiranico.com"
languages = [
    "en",
    "ja",
    "fr",
    "it",
    "de",
    "es",
    "ru",
    "pl",
    "ko",
    "zh-Hant",
    "zh"
]

URL = urllib.parse.urljoin(baseURL, languages[0])
URL = urllib.parse.urljoin(URL, "data/rampage-skills")
r = requests.get(URL)
r.encoding = "utf-8"

skills = []
soup = BeautifulSoup(r.text, features="lxml")
raw_skills = soup.find_all(href=re.compile(r"https://mhrise.kiranico.com/data/rampage-skills/\d+"))
paired_skills = [[j.contents[0].strip() for j in i.find_all(class_="text-sm")] for i in raw_skills]

for i in range(len(paired_skills)):
    skill = paired_skills[i]
    str_expr = re.compile(r"[\:\(\)]")
    entry = {
        "id": i + 1,
        "name": "_".join(
            str_expr.sub("", i.lower())
             .replace("-", "_")
            for i in skill[0].split()
        ),
        "name_entry": [{
            "text": skill[0],
            "language": "en"
        }],
        "description_entry": [{
            "text": skill[1],
            "language": "en"
        }],
    }
    skills.append(entry)

for lang in languages[1:]:
    URL = urllib.parse.urljoin(baseURL, f"{lang}/data/rampage-skills")
    r = requests.get(URL)
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, features="lxml")
    expr = f"https://mhrise.kiranico.com/{lang}/data/rampage-skills/\d+"

    raw_skills = soup.find_all(href=re.compile(expr))
    paired_skills = [[j.contents[0].strip() for j in i.find_all(class_="text-sm")] for i in raw_skills]
    for i in range(len(paired_skills)):
        skill = paired_skills[i]
        nameEntry = {
            "text": skill[0],
            "language": lang
        }
        descriptionEntry = {
            "text": skill[1],
            "language": lang
        }
        skills[i]["name_entry"].append(nameEntry)
        skills[i]["description_entry"].append(descriptionEntry)

with open("json/rampage_skill.json", "w", encoding="utf-8") as f:
    json.dump(skills, f)