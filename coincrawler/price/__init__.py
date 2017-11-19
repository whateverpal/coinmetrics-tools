import requests
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from dateutil import parser as dateutilParser

cmcTickerTranslation = {
	"btc": "bitcoin", 
	"bch": "bitcoin-cash",
	"ltc": "litecoin", 
	"xem": "nem", 
	"dash": "dash", 
	"xmr": "monero", 
	"dcr": "decred", 
	"eth": "ethereum", 
	"zec": "zcash", 
	"doge": "dogecoin", 
	"etc": "ethereum-classic", 
	"pivx": "pivx",
	"vtc": "vertcoin"
}

def downloadUsdPriceData(currency, db, fillHoles=False):
	priceStorageAccess = db.getPriceStorageAccess(currency)
	priceStorageAccess.flushPrices()

	dateNow = datetime.now()
	year = str(dateNow.year)
	month = str(dateNow.month)
	if len(month) < 2:
		month = "0" + month
	day = str(dateNow.day)
	if len(day) < 2:
		day = "0" + day
	endDate = year + month + day
	startDate = "20100101" if currency != "bch" else "20170731"
	r = requests.get("https://coinmarketcap.com/currencies/%s/historical-data/?start=%s&end=%s" % (cmcTickerTranslation[currency], startDate, endDate), timeout=30)
	soup = BeautifulSoup(r.text, 'html.parser')

	rows = soup.find("div", id="historical-data").find_all("tr", class_="text-right")
	result = []
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
		result.append((date, price, marketcap, volume))

	if fillHoles:
		while True:
			holesFound = False
			prevDate = result[0][0]
			index = 1
			for row in result[1:]:
				diff = row[0] - prevDate
				if diff > timedelta(days=1):
					holesFound = True
					print "Missing price for %s" % (prevDate + timedelta(days=1))
					result.insert(index, (prevDate + timedelta(days=1), row[1], row[2], row[3]))
					break
				prevDate = row[0]
				index += 1

			if not holesFound:
				break

		
	priceStorageAccess.storePrices(result)