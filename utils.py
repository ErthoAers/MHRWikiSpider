import re

baseURL = "http://mhrise.mhrice.info"
en_tag = "mh-lang-1"

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

weapon_list = {
    "great_sword": 0,
    "long_sword": 3,
    "short_sword": 1,
    "dual_blades": 2,
    "hammer": 4,
    "horn": 5,
    "lance": 6,
    "gun_lance": 7,
    "slash_axe": 8,
    "charge_axe": 9,
    "insect_glaive": 10,
    "light_bowgun": 13,
    "heavy_bowgun": 12,
    "bow": 11
}

def camel_to_snake(text):
    text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()

item_id = {}
armor_id = {}
weapon_id = {}
item_crafting = {}