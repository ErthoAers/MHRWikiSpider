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


def camel_to_snake(text):
    text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', text).lower()