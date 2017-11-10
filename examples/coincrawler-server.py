from coincrawler.blocks.datasources import *
from coincrawler import BlockCollectionServer

# this server is able to fetch blocks for all supported cryptocurrencies
# here we specify data source for each one
# mind the lambda!
dataSources = {
	# bitcoin-like cryptocurrencies' data can be fetched from node via RPC API
	# pass address, port, user, password, number of blocks to prefetch (recommended 1 for big blockchains and 5-10 for small) and path to the folder which will contain LMDB cache
	"btc": 	lambda: BitcoinBlockchainDataSource("localhost", 35753, "rpcuser", "rpcpassword", 1, useLMDBCache=True, lmdbCachePath="/path/to/btc/cache"),
	"bch": 	lambda: BitcoinBlockchainDataSource("localhost", 35853, "rpcuser", "rpcpassword", 1, useLMDBCache=True, lmdbCachePath="/path/to/bch/cache"),
	"dash": lambda: BitcoinBlockchainDataSource("localhost", 20004, "rpcuser", "rpcpassword", 10, useLMDBCache=True, lmdbCachePath="/path/to/dash/cache"),
	"zec": 	lambda: BitcoinBlockchainDataSource("localhost", 13333, "rpcuser", "rpcpassword", 5, useLMDBCache=True, lmdbCachePath="/path/to/zcash/cache"),
	"doge": lambda: BitcoinBlockchainDataSource("localhost", 19999, "rpcuser", "rpcpassword", 10, useLMDBCache=True, lmdbCachePath="/path/to/doge/cache"),
	"ltc": 	lambda: BitcoinBlockchainDataSource("localhost", 20002, "rpcuser", "rpcpassword", 10, useLMDBCache=True, lmdbCachePath="/path/to/ltc/cache"),
	"vtc": 	lambda: BitcoinBlockchainDataSource("localhost", 20005, "rpcuser", "rpcpassword", 20, useLMDBCache=True, lmdbCachePath="/path/to/vtc/cache"),
	# for PIVX, pass isPivx=True
	"pivx": lambda: BitcoinBlockchainDataSource("localhost", 20005, "rpcuser", "rpcpassword", 20, useLMDBCache=True, lmdbCachePath="/path/to/pivx/cache", isPivx=True),
	
	# ETC and Monero data sources rely on geth / monero RPC API
	"etc": 	lambda: EthereumClassicBlockchainDataSource("localhost", 8545),
	"xmr": 	lambda: MoneroBlockchainDataSource("localhost", 18081),

	# Ethereum data can be fetched either the same way as ETC or from etherchain.org block explorer
	"eth": 	lambda: EtherChainDataSource(), # or lambda: EthereumBlockchainDataSource()

	# XEM and DCR are fetched from block explorers
	"xem": 	lambda: NemNinjaDataSource(),
	"dcr": 	lambda: MainnetDecredOrgDataSource(),
}

# etherchain block explorer limits amount of requsts per second, this will add 12 seconds delay between requests
dataSourcesSleepBetweenRequests = {
	"eth": 12
}

# run block collection server on port 13333 until keyboard interrupt is received
BlockCollectionServer(13333, dataSources, dataSourcesSleepBetweenRequests).run()