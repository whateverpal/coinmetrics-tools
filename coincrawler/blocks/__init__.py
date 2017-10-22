from coincrawler.db import DBAccess
from storage import PostgresDBStorage
from datasources import *
from downloaders import *
from datetime import datetime
import os

mineableCurrencyColumns = ["height", "timestamp", "txVolume", "txCount", "generatedCoins", "fees", "difficulty"]
nonmineableCurrencyColumns = ["height", "timestamp", "txVolume", "txCount", "fees"]

def fetchBlocksFromServers(currency, hostsAndPorts, sleepBetweenRequests, countPerJob, db, stopSignal=None):
	columns = nonmineableCurrencyColumns if currency == "xem" else mineableCurrencyColumns
	storage = PostgresDBStorage(currency, columns, db)
	downloaders = []
	for host, port in hostsAndPorts:
		downloader = NetworkDownloader(currency, host, port, sleepBetweenRequests=sleepBetweenRequests, amountPerRequest=countPerJob)
		downloaders.append(downloader)
	downloader = MultisourceDownloader(downloaders, countPerJob, 300, len(hostsAndPorts) * 2)
	
	try:
		networkBlockHeight = downloader.getBlockHeight()
		dbBlockHeight = storage.getBlockHeight()
		print "db blocks: %s, network blocks: %s" % (dbBlockHeight, networkBlockHeight)

		blocksToLoad = range(dbBlockHeight + 1, networkBlockHeight + 1)

		if len(blocksToLoad) > 0:
			for block in downloader.loadBlocks(blocksToLoad):
				if type(block["timestamp"]) != datetime:
					block["timestamp"] = datetime.utcfromtimestamp(block["timestamp"])
				storage.storeBlock(block)

				if stopSignal is not None and stopSignal():
					print "stop signal received, aborting"
					return
					
		print "sync done"
	except KeyboardInterrupt:
		print "keyboard interrupt received, exiting"
		os._exit(1)
