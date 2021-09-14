# import requests
# import re
# from bs4 import BeautifulSoup
# import urllib.parse
# import json
# import multiprocessing.pool
# from utils import *

# links = []
# monsterListURL = urllib.parse.urljoin(baseURL, "monster.html")
# r = requests.get(monsterListURL)
# r.encoding = "utf-8"

# expr = r"^/monster/(\d{3})_(\d{2}).html$"
# soup = BeautifulSoup(r.text, features="lxml")
# links = [i["href"] for i in soup.find_all(href=re.compile(expr))]
# monster = []

# for link in links:
#     expr = r"^/monster/(\d{3})_(\d{2}).html$"
#     match = re.match(expr, link)
#     monster_id = int(match.group(1))
#     monster_subid = int(match.group(2))
#     monsterURL = urllib.parse.urljoin(baseURL, link)
#     r = requests.get(monsterURL)
#     r.encoding = "utf-8"
#     soup = BeautifulSoup(r.text, features="lxml")
#     section = soup.find_all("section")
#     quests = section[1]
#     for q in quests.find("tbody").find_all("tr"):
#         f = q.find_all("td")
#         if f[6].text != f[7].text:
#             print(monster_id, monster_subid)

# from functools import lru_cache
# import time

# def knightDialer1(n):
#     mod = int(1e9) + 7
#     prev = [1] * 10
#     for i in range(n - 1):
#         prev = [
#             (prev[4] + prev[6]) % mod,
#             (prev[6] + prev[8]) % mod,
#             (prev[7] + prev[9]) % mod,
#             (prev[4] + prev[8]) % mod,
#             (prev[3] + prev[9] + prev[0]) % mod,
#             0,
#             (prev[1] + prev[7] + prev[0]) % mod,
#             (prev[2] + prev[6]) % mod,
#             (prev[1] + prev[3]) % mod,
#             (prev[2] + prev[4]) % mod
#         ]
        
#     return sum(prev) % mod

# def knightDialer(n: int) -> int:
#     mod = int(1e9) + 7

#     def helper(*nums):
#         r = [0] * 10
#         for num in nums:
#             r[num] = 1
#         return r

#     states = [
#         helper(4, 6),
#         helper(6, 8),
#         helper(7, 9),
#         helper(4, 8),
#         helper(0, 3, 9),
#         helper(),
#         helper(0, 1, 7),
#         helper(2, 6),
#         helper(1, 3),
#         helper(2, 4),
#     ]


#     @lru_cache(None)
#     def dp(n, start):
#         if n == 0:
#             return helper(start)
#         if n == 1:
#             return states[start]
#         prev1 = dp(n // 2, start)
#         prev2 = [dp(n - n // 2, i) for i in range(10)]
#         mat = [[prev1[i] * j for j in prev2[i]] for i in range(10)]
#         return [sum(k) % mod for k in zip(*mat)]

#     return sum(sum(dp(n - 1, i)) for i in range(10)) % mod

# n = int(1.7976931348623158e308)
# import sys
# sys.setrecursionlimit(65536)

# start_time = time.time()
# print(knightDialer(n))
# print(f"Log Time: {time.time() - start_time:.3f}")

# start_time = time.time()
# knightDialer1(n)
# print(f"Linear Time: {time.time() - start_time:.3f}")


l01 = [16, 20, 45, 11, 3, 71, 7, 33, 2, 0, 2]
l = [0] * 11
l1 = [55, 52]
l2 = [1, 1]
name = "九亿少女"
while True:
    s = input()
    if s == "#":
        break
    n1, n2 = s.split()
    n1, n2 = int(n1), int(n2)
    l[n1] += 1
    l[n2] += 1

print(l)
