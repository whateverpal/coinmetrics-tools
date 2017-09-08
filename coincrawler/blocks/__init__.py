from coincrawler.db import DBAccess
from storage import PostgresDBStorage
from datasources import *
from downloaders import *
from datetime import datetime
import os

def fetchBlocksFromServers(currency, hostsAndPorts, sleepBetweenRequests, countPerJob, db):
	columns = nonmineableCurrencySupportedData if currency == "xem" else mineableCurrencySupportedData
	storage = PostgresDBStorage(currency, columns, db)
	downloaders = []
	for host, port in hostsAndPorts:
		downloader = NetworkDownloader(currency, host, port, sleepBetweenRequests=sleepBetweenRequests, amountPerRequest=countPerJob)
		downloaders.append(downloader)
	downloader = MultisourceDownloader(downloaders, countPerJob, 300, len(hostsAndPorts) * 2)
	fetchBlocks(storage, downloader)


mineableCurrencySupportedData = ["height", "timestamp", "txVolume", "txCount", "generatedCoins", "fees", "difficulty"]
nonmineableCurrencySupportedData = ["height", "timestamp", "txVolume", "txCount", "fees"]


def fetchBlocks(storage, dataDownloader):
	try:
		networkBlockHeight = dataDownloader.getBlockHeight()
		dbBlockHeight = storage.getBlockHeight()
		print "db blocks: %s, network blocks: %s" % (dbBlockHeight, networkBlockHeight)

		blocksToLoad = range(dbBlockHeight + 1, networkBlockHeight + 1)

		if len(blocksToLoad) > 0:
			for block in dataDownloader.loadBlocks(blocksToLoad):
				if type(block["timestamp"]) != datetime:
					block["timestamp"] = datetime.utcfromtimestamp(block["timestamp"])
				storage.storeBlock(block)
		print "sync done"
	except KeyboardInterrupt:
		print "keyboard interrupt received, exiting"
		os._exit(1)