from downloaders import NetworkDownloader, MultisourceDownloader
from datetime import datetime
import os

mineableCurrencyColumns = ["height", "timestamp", "txVolume", "txCount", "generatedCoins", "fees", "difficulty"]
nonmineableCurrencyColumns = ["height", "timestamp", "txVolume", "txCount", "fees"]

def fetchBlocksFromServers(currency, hostsAndPorts, sleepBetweenRequests, countPerJob, storage, stopSignal=None):
	columns = nonmineableCurrencyColumns if currency == "xem" else mineableCurrencyColumns
	blockStorageAccess = storage.getBlockStorageAccess(currency, columns)
	downloaders = []
	for host, port in hostsAndPorts:
		downloader = NetworkDownloader(currency, host, port, sleepBetweenRequests=sleepBetweenRequests, amountPerRequest=countPerJob)
		downloaders.append(downloader)
	downloader = MultisourceDownloader(downloaders, countPerJob, 300, len(hostsAndPorts) * 2)
	
	try:
		networkBlockHeight = downloader.getBlockHeight()
		dbBlockHeight = blockStorageAccess.getBlockHeight()
		print "db blocks: %s, network blocks: %s" % (dbBlockHeight, networkBlockHeight)

		blocksToLoad = range(dbBlockHeight + 1, networkBlockHeight + 1)

		if len(blocksToLoad) > 0:
			for block in downloader.loadBlocks(blocksToLoad):
				if type(block["timestamp"]) != datetime:
					block["timestamp"] = datetime.utcfromtimestamp(block["timestamp"])
				blockStorageAccess.storeBlock(block)

				if stopSignal is not None and stopSignal():
					print "stop signal received, syncing will be aborted"
					downloader.stop()
					
		print "sync done"
	except KeyboardInterrupt:
		print "keyboard interrupt received, exiting"
		os._exit(1)
