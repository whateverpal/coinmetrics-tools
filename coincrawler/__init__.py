import time
import os

from coincrawler.blocks import fetchBlocksFromServers
from coincrawler.price import downloadUsdPriceData
from coincrawler.db import DBAccess
from coincrawler.blocks.jobserver import JobServer
from coincrawler.dump import dumpDailyStatsToCSV

def runJobServer(port, dataSources, dataSourcesSleepBetweenRequests):
	js = JobServer(port, dataSources, dataSourcesSleepBetweenRequests)
	js.start()
	while True:
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			js.stop()
			os._exit(1)