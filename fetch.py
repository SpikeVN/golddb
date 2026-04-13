# %%
import requests
import bs4
import pandas as pd
import orjson
import chompjs
import numpy as np
import datetime
import dataclasses
import xml.etree.ElementTree as ET
import time
import os

@dataclasses.dataclass
class Price24K:
    buy_bullion: int
    sell_bullion: int
    buy_ring: int
    sell_ring: int
    taken_on: datetime.datetime
    vendor: str = ""

# %%
def sjc_onemonth() -> pd.DataFrame:
    soup = bs4.BeautifulSoup(requests.get("https://giavang.org").text, "html.parser")
    data = chompjs.parse_js_object(soup.find_all("script")[13].text.split("\n")[2].replace("    var seriesOptions = ", "")[:-1])

    return pd.DataFrame(
        {
            "buy": np.array(data[0]["data"])[:, 1],
            "sell": np.array(data[1]["data"])[:, 1],
        },
        index=pd.DatetimeIndex([datetime.datetime.fromtimestamp(i/1000).date().isoformat() for i, _ in data[0]["data"]])
    )

# %%
def sjc_threemonths() -> pd.DataFrame:
    soup = bs4.BeautifulSoup(requests.get("https://giavang.org/trong-nuoc/sjc").text, "html.parser")
    data = chompjs.parse_js_object(soup.find_all("script")[15].text.split("\n")[2].replace("    var seriesOptions = ", "")[:-1])

    return pd.DataFrame(
        {
            "buy": np.array(data[0]["data"])[:, 1],
            "sell": np.array(data[1]["data"])[:, 1],
        },
        index=pd.DatetimeIndex([datetime.datetime.fromtimestamp(i/1000).date().isoformat() for i, _ in data[0]["data"]])
    )

# %%
def sjc_today() -> Price24K:
    buy_bullion: int = 0
    sell_bullion: int = 0
    buy_ring: int = 0
    sell_ring: int = 0
    with requests.Session() as s:
        data = s.get("https://sjc.com.vn/GoldPrice/Services/PriceService.ashx", headers={
            "origin": "https://sjc.com.vn",
            "priority": "u=1, i",
            "referer": "https://sjc.com.vn/bieu-do-gia-vang",
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Microsoft Edge";v="144"',
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36 Edg/144.0.0.0",
            "x-requested-with": "XMLHttpRequest"
        }).json()
        for i in data["data"]:
            if i["TypeName"] == "Vàng SJC 1L, 10L, 1KG" and i["BranchName"] == "Hồ Chí Minh":
                buy_bullion = int(i["BuyValue"])
                sell_bullion = int(i["SellValue"])
            if i["TypeName"] == "Vàng nhẫn SJC 99,99% 1 chỉ, 2 chỉ, 5 chỉ" and i["BranchName"] == "Hồ Chí Minh":
                buy_ring = int(i["BuyValue"])
                sell_ring = int(i["SellValue"])
        return Price24K(
            buy_bullion, sell_bullion, buy_ring, sell_ring, taken_on=datetime.datetime.now(), vendor="SJC"
        )

# %%
def doji_today() -> Price24K:
    req = requests.get("http://giavang.doji.vn/api/giavang/?api_key=258fbd2a72ce8481089d88c678e9fe4f")
    req.encoding = "utf8"
    root = ET.fromstring(req.text)
    buy_bullion: int = 0
    sell_bullion: int = 0
    buy_ring: int = 0
    sell_ring: int = 0
    for tag in root.findall("DGPlist/Row"):
        if "Key" in tag.attrib and tag.attrib["Key"] == "dojihanoile":
            sell_bullion = int(1_000_000 * float(tag.attrib["Sell"].replace(",", ".")))
            buy_bullion = int(1_000_000 * float(tag.attrib["Buy"].replace(",", ".")))
            break

    for tag in root.findall("JewelryList/Row"):
        if "Key" in tag.attrib and tag.attrib["Key"] == "nhanhung1chi":
            sell_ring = int(10_000_000 * float(tag.attrib["Sell"].replace(",", ".")))
            buy_ring = int(10_000_000 * float(tag.attrib["Buy"].replace(",", ".")))
            break
    return Price24K(
        buy_bullion, sell_bullion, buy_ring, sell_ring, taken_on=datetime.datetime.now(), vendor="DOJI"
    )

# %%
def pnj_today() -> Price24K:
    buy_bullion: int = 0
    sell_bullion: int = 0
    buy_ring: int = 0
    sell_ring: int = 0
    data = requests.get("https://edge-api.pnj.io/ecom-frontend/v1/get-gold-price?zone=00").json()
    for i in data["data"]:
        if i["masp"] == "N24K":
            sell_ring = i["giaban"]*10000
            buy_ring = i["giamua"]*10000
        if i["masp"] == "KB":
            sell_bullion = i["giaban"]*10000
            buy_bullion = i["giamua"]*10000
    return Price24K(
        buy_bullion, sell_bullion, buy_ring, sell_ring, taken_on=datetime.datetime.now(), vendor="PNJ"
    )

# %%
def btmc_today() -> Price24K:
    soup = bs4.BeautifulSoup(requests.get("https://btmc.vn/gia-vang-theo-ngay.html").text, "html.parser")
    bullion = list(list(soup.find_all(class_="bd_price_home")[0].children)[1].children)[3]  # type: ignore
    ring = list(list(soup.find_all(class_="bd_price_home")[0].children)[1].children)[4]  # type: ignore
    return Price24K (
        taken_on=datetime.datetime.now(),
        buy_bullion = int(list(bullion.children)[7].getText().strip()) * 10000,
        sell_bullion = int(list(bullion.children)[9].getText().strip()) * 10000,
        buy_ring = int(list(ring.children)[5].getText().strip()) * 10000,
        sell_ring = int(list(ring.children)[7].getText().strip()) * 10000,
        vendor="BTMC"
    )

# %%
def btmh_today() -> Price24K:
    soup = bs4.BeautifulSoup(requests.get("https://baotinmanhhai.vn/gia-vang-hom-nay").text, "html.parser")
    price_table = list(list(soup.find_all(class_="gold-table-content")[0].children)[3].children)  # type: ignore
    return Price24K (
        taken_on=datetime.datetime.now(),
        buy_ring = int(list(price_table[1].children)[3].text.replace(".", "").strip()) * 10,
        sell_ring = int(list(price_table[1].children)[5].text.replace(".", "").strip()) * 10,
        buy_bullion = int(list(price_table[5].children)[3].text.replace(".", "").strip()) * 100,
        sell_bullion = int(list(price_table[5].children)[5].text.replace(".", "").strip()) * 100,
        vendor="BTMH"
    )

# %%
def pqg_today() -> Price24K:
    soup = bs4.BeautifulSoup(requests.get("https://phuquygroup.vn/").text, "html.parser")
    price_table = list(soup.select_one("#priceList table").select("tr"))  # type: ignore
    return Price24K (
        taken_on=datetime.datetime.now(),
        buy_ring = int(price_table[2].select_one("td.buy-price").text.strip().replace(",", "")) * 10,  # type: ignore
        sell_ring = int(price_table[2].select_one("td.sell-price").text.strip().replace(",", "")) * 10,  # type: ignore
        buy_bullion = int(price_table[3].select_one("td.buy-price").text.strip().replace(",", "")) * 10,  # type: ignore
        sell_bullion = int(price_table[3].select_one("td.sell-price").text.strip().replace(",", "")) * 10,  # type: ignore,
        vendor="PQG",
    )

# %%
def mihong_today() -> Price24K:
    s = requests.Session()
    buy_bullion = 0
    sell_bullion = 0
    buy_ring = 0
    sell_ring = 0
    s.get("http://mihong.vn/vi/gia-vang-trong-nuoc")
    data = s.get('https://mihong.vn/api/v1/gold/prices/current', headers={
        'Host': 'mihong.vn',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://mihong.vn/vi/gia-vang-trong-nuoc',
    }, verify=False).json()
    for i in data["data"]:
        if i["code"] == "999":
            buy_bullion = buy_ring = i["buyingPrice"] * 10
            sell_ring = sell_bullion = i["sellingPrice"] * 10

    return Price24K(
        taken_on=datetime.datetime.now(),
        buy_bullion=buy_bullion,
        sell_bullion=sell_bullion,
        buy_ring=buy_ring,
        sell_ring=sell_ring,
        vendor="MHG"
    )

# %%
def ngoctham_today() -> Price24K:
    s = bs4.BeautifulSoup(requests.get("https://ngoctham.com/bang-gia-vang/").text)
    ring = list(s.find_all("tr", attrs={"data-id": "61"})[1].children)
    bullion = list(s.find_all("tr", attrs={"data-id": "60"})[1].children)

    return Price24K(
        taken_on=datetime.datetime.now(),
        buy_bullion = int(bullion[3].text.strip().replace(".", "")) * 10,
        sell_bullion = int(bullion[5].text.strip().replace(".", "")) * 10,
        buy_ring = int(ring[3].text.strip().replace(".", "")) * 10,
        sell_ring = int(ring[5].text.strip().replace(".", "")) * 10,
        vendor="NTH",
    )

# %%
def fetch_all() -> list[Price24K]:
    results = []
    print(f"            vendor  buy bullion    sell bullion    buy ring      sell ring")
    #       [*] fetched    SJC  173000000      173000000       173000000     173000000
    for fetch_method in [sjc_today, doji_today, pnj_today, btmc_today, btmh_today, pqg_today, mihong_today, ngoctham_today]:
        def fetch(tries = 10):
            try:
                return fetch_method()
            except requests.ConnectionError:
                if tries > 0:
                    print(f"Fetch failed for {fetch_method.__name__}. Retrying after 5s (attempt {10 - tries + 1}/10).")
                    time.sleep(5)
                    return fetch(tries-1)
                raise
            except:
                print(f"[!] fetching {fetch_method.__name__} failed")
        d = fetch()
        if d:
            results.append(d)
            print(f"[*] fetched    {d.vendor:>4}  {d.buy_bullion}      {d.sell_bullion}       {d.buy_ring}     {d.sell_ring}")
            with open(os.path.join("data", "snapshotdb.csv"), "a", encoding="utf8") as f:
                f.write(f"{d.taken_on.isoformat()},{d.vendor},{d.buy_bullion},{d.sell_bullion},{d.buy_ring},{d.sell_ring}\n")
    return results

def run_cron():
    with open(os.path.join("data", "master.json"), "r", encoding="utf8") as f:
        contents = f.read()
        data = []
        if contents.strip() != "":
            data = orjson.loads(contents)
        data.append({
            "takenOn": datetime.datetime.now().isoformat(),
            "prices": fetch_all()
        })
    with open(os.path.join("data", "master.json"), "w", encoding="utf8") as f:
        f.buffer.write(orjson.dumps(data))
        f.buffer.flush()

# %%
run_cron()


