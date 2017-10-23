# example of fetching bitcoin blocks from coincrawler-server
from coincrawler import fetchBlocksFromServers, downloadUsdPriceData, dumpDailyStatsToCSV, PostgresStorage

# create connection with Postgres database, specify database host, name, user and password
storage = PostgresStorage("dbhost", "dbname", "dbuser", "dbpassword")

currency = "btc"

# fetch BTC blocks from server
fetchBlocksFromServers(
	currency,
	[("localhost", 13333)], # we have a single coincrawler server running on the same machine on port 13333
	1,	# will poll server every second
	10, # server will deliver batches of 10 blocks,
	storage
)

# fetch price, exchange volume from coinmarketcap
downloadUsdPriceData(currency, storage)

# dump daily stats to csv/btc.csv
dumpDailyStatsToCSV(currency, storage)
