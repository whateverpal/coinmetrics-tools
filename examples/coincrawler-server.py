from coincrawler.blocks.datasources import *
from coincrawler import BlockCollectionServer

# this server is able to fetch blocks for all supported cryptocurrencies
# here we specify data source for each one
# mind the lambda!
dataSources = {
	# bitcoin-like cryptocurrencies' data can be fetched from node via RPC API
	# pass address, port, user, password, number of blocks to prefetch (recommended 1 for big blockchains and 5-10 for small) and path to the folder which will contain LMDB cache
	# by default, 10 last blocks won't be collected in order to avoid reorganizations, use dropBlocksCount param to influence this behavior
	"btc": 	lambda: BitcoinBlockchainDataSource("localhost", 35753, "rpcuser", "rpcpassword", 1, useLMDBCache=True, lmdbCachePath="/path/to/btc/cache"),
	"bch": 	lambda: BitcoinBlockchainDataSource("localhost", 35853, "rpcuser", "rpcpassword", 1, useLMDBCache=True, lmdbCachePath="/path/to/bch/cache"),
	"btg": 	lambda: BitcoinBlockchainDataSource("localhost", 35853, "rpcuser", "rpcpassword", 1, useLMDBCache=True, lmdbCachePath="/path/to/btg/cache"),
	"dash": lambda: BitcoinBlockchainDataSource("localhost", 20004, "rpcuser", "rpcpassword", 10, useLMDBCache=True, lmdbCachePath="/path/to/dash/cache"),
	"zec": 	lambda: BitcoinBlockchainDataSource("localhost", 13333, "rpcuser", "rpcpassword", 5, useLMDBCache=True, lmdbCachePath="/path/to/zcash/cache"),
	"doge": lambda: BitcoinBlockchainDataSource("localhost", 19999, "rpcuser", "rpcpassword", 10, useLMDBCache=True, lmdbCachePath="/path/to/doge/cache"),
	"ltc": 	lambda: BitcoinBlockchainDataSource("localhost", 20002, "rpcuser", "rpcpassword", 10, useLMDBCache=True, lmdbCachePath="/path/to/ltc/cache"),
	"vtc": 	lambda: BitcoinBlockchainDataSource("localhost", 20005, "rpcuser", "rpcpassword", 20, useLMDBCache=True, lmdbCachePath="/path/to/vtc/cache"),
	"xvg": 	lambda: BitcoinBlockchainDataSource("localhost", 20006, "rpcuser", "rpcpassword", 20, useLMDBCache=True, lmdbCachePath="/path/to/xvg/cache"),
	# digibyte blockchain has 15 seconds block time, notice that we instruct collection to ignore 400 last blocks to avoid reorganizations
	"dgb": 	lambda: BitcoinBlockchainDataSource("localhost", 20007, "rpcuser", "rpcpassword", 20, useLMDBCache=True, lmdbCachePath="/path/to/dgb/cache", dropBlocksCount=400),
	# for PIVX, pass isPivx=True
	"pivx": lambda: BitcoinBlockchainDataSource("localhost", 20005, "rpcuser", "rpcpassword", 20, useLMDBCache=True, lmdbCachePath="/path/to/pivx/cache", isPivx=True),
	
	# ETH, ETC and Monero data sources rely on geth / monero RPC API
	"eth": 	lambda: EthereumBlockchainDataSource("localhost", 8546),
	"etc": 	lambda: EthereumClassicBlockchainDataSource("localhost", 8545),
	"xmr": 	lambda: MoneroBlockchainDataSource("localhost", 18081),

	# XEM and DCR are fetched from block explorers
	"xem": 	lambda: NemNinjaDataSource(),
	"dcr": 	lambda: MainnetDecredOrgDataSource(),
}

# run block collection server on port 13333 until keyboard interrupt is received
BlockCollectionServer("127.0.0.1", 13333, dataSources).run()