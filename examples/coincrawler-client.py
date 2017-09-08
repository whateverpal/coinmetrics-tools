# example of fetching bitcoin blocks from coincrawler-server
from coincrawler import fetchBlocksFromServers, downloadUsdPriceData, dumpDailyStatsToCSV, DBAccess

# create connection with database, specify database name, user and password
db = DBAccess("dbname", "dbuser", "dbpassword")

currency = "btc"

# fetch BTC blocks from server
fetchBlocksFromServers(
	currency,
	[("localhost", 13333)], # we have a single coincrawler server running on the same machine on port 13333
	1,	# will poll server every second
	10, # server will deliver batches of 10 blocks,
	db
)

# fetch price, exchange volume from coinmarketcap
downloadUsdPriceData(currency, db)

# dump daily stats to csv/xem.csv
dumpDailyStatsToCSV(currency, db)
