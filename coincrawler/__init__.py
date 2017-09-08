from datetime import timedelta, datetime
import time
import os

from coincrawler.blocks import fetchBlocksFromServers
from coincrawler.price import downloadUsdPriceData
from coincrawler.db import DBAccess
from coincrawler.blocks.jobserver import JobServer

def dumpDailyStatsToCSV(currency, db):
	blocksTableName = "blocks_" + currency
	blocks = db.queryReturnAll("SELECT timestamp, txVolume, txCount FROM " + blocksTableName)
	pricesTableName = "priceUsd_" + currency
	prices = db.queryReturnAll("SELECT timestamp, price, marketCap, totalExchangeVolume FROM " + pricesTableName)

	txVolumeByDay = {}
	txCountByDay = {}
	for block in blocks:
		blockTimestamp = block[0].replace(second=0, microsecond=0, hour=0, minute=0) + timedelta(days=1)
		intTimestamp = int((blockTimestamp - datetime(1970, 1, 1)).total_seconds())
		if not intTimestamp in txVolumeByDay:
			txVolumeByDay[intTimestamp] = 0.0
			txCountByDay[intTimestamp] = 0
		txVolumeByDay[intTimestamp] += float(block[1])
		txCountByDay[intTimestamp] += float(block[2])

	allData = []
	for date, price, marketcap, exchangeVolume in prices:
		row = [date]
		intTimestamp = int((date - datetime(1970, 1, 1)).total_seconds())
		if intTimestamp in txVolumeByDay:
			row.append(str(txVolumeByDay[intTimestamp] * float(price)))
			row.append(str(txCountByDay[intTimestamp]))
			row.append(str(float(price)))
			row.append(str(float(marketcap)))
			row.append(str(float(exchangeVolume)))
			allData.append(row)
		else:
			print "missing timestamp for %s: %s" % (currency, str(intTimestamp))
	allData = sorted(allData, key=lambda elem: elem[0])
	if currency == "eth":
		allData.pop()

	f = open("csv/%s.csv" % currency, "w")
	f.write("date,txVolume(USD),txCount,marketcap(USD),price(USD),exchangeVolume(USD)\n")
	for date, txVolume, txCount, price, mcap, exchangeVolume in allData:
		f.write(date.strftime('%Y/%m/%d') + ",")
		f.write(",".join([str(txVolume), str(txCount), str(mcap), str(price), str(exchangeVolume)]))
		f.write(",")
		f.write("\n")
	f.close()

	print "%s dump done" % currency


def runJobServer(port, dataSources, dataSourcesSleepBetweenRequests):
	js = JobServer(port, dataSources, dataSourcesSleepBetweenRequests)
	js.start()
	while True:
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			js.stop()
			os._exit(1)