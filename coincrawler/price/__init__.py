import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil import parser as dateutilParser

from coincrawler.db import DBAccess

def downloadUsdPriceData(currency, db):
	db.queryNoReturnCommit("truncate table priceUsd_" + currency)

	cmcTickerTranslation = {
		"btc": "bitcoin", 
		"ltc": "litecoin", 
		"xem": "nem", 
		"dash": "dash", 
		"xmr": "monero", 
		"dcr": "decred", 
		"eth": "ethereum", 
		"zec": "zcash", 
		"doge": "dogecoin", 
		"etc": "ethereum-classic", 
		"pivx": "pivx"
	}
	r = requests.get("https://coinmarketcap.com/currencies/%s/historical-data/?start=20100101&end=20990902" % cmcTickerTranslation[currency])
	soup = BeautifulSoup(r.text, 'html.parser')

	rows = soup.find("div", id="historical-data").find_all("tr", class_="text-right")
	for row in rows[::-1]:
		tds = row.find_all("td")

		volume = tds[5].text
		if volume == "-":
			volume = 0.0
		else:
			volume = float(volume.replace(",", ""))

		marketcap = tds[6].text
		if marketcap == "-":
			marketcap = 0.0
		else:
			marketcap = float(marketcap.replace(",", ""))

		date = dateutilParser.parse(tds[0].text)
		price = float(tds[4].text.replace(",", ""))
		db.queryNoReturnNoCommit("INSERT INTO priceUsd_" + currency + " (timestamp, price, marketcap, totalExchangeVolume) VALUES (%s, %s, %s, %s)", 
				(date, price, marketcap, volume))
	db.commit()