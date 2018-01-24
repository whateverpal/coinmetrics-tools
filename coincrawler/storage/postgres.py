from coincrawler.storage import IStorage, IBlockStorageAccess, IPriceStorageAccess

mineableCurrencyColumns = ["height", "timestamp", "txVolume", "txCount", "generatedCoins", "fees", "difficulty"]
nonmineableCurrencyColumns = ["height", "timestamp", "txVolume", "txCount", "fees"]

class PostgresStorage(IStorage):

	def __init__(self, dbHost, dbName, dbUser, dbPassword):
		import psycopg2
		self.connection = psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (dbHost, dbName, dbUser, dbPassword))
		self.cursor = self.connection.cursor()

	def __del__(self):
		self.close()

	def queryNoReturnCommit(self, text, params=None):
		self.cursor.execute(text, params)
		self.connection.commit()

	def queryNoReturnNoCommit(self, text, params=None):
		self.cursor.execute(text, params)

	def queryReturnOne(self, text, params=None):
		self.cursor.execute(text, params)
		return self.cursor.fetchone()

	def queryReturnAll(self, text, params=None):
		self.cursor.execute(text, params)
		return self.cursor.fetchall()

	def commit(self):
		self.connection.commit()

	def close(self):
		self.cursor.close()
		self.connection.close()

	def getBlockStorageAccess(self, currency):
		columns = mineableCurrencyColumns if currency != "xem" else nonmineableCurrencyColumns
		return PostgresStorageBlockAccess(currency, columns, self)

	def getPriceStorageAccess(self, currency):
		return PostgresPriceStorageAccess(currency, self)


class PostgresStorageBlockAccess(IBlockStorageAccess):

	BLOCK_TABLE_COLUMNS = {
		"height": "INTEGER PRIMARY KEY",
		"timestamp": "TIMESTAMP",
		"txVolume": "NUMERIC",
		"txCount": "INTEGER",
		"generatedCoins": "NUMERIC",
		"fees": "NUMERIC",
		"difficulty": "NUMERIC",
	}

	def __init__(self, ticker, columns, db):
		self.db = db
		self.ticker = ticker
		self.columns = columns
		self.tableName = "blocks_" + self.ticker

		columnsText = ", ".join([column + " " + PostgresStorageBlockAccess.BLOCK_TABLE_COLUMNS[column] for column in self.columns])
		self.db.queryNoReturnCommit("CREATE TABLE IF NOT EXISTS %s (%s)" % (self.tableName, columnsText))

	def getBlockHeight(self):
		result = self.db.queryReturnAll("SELECT height FROM %s ORDER BY height DESC LIMIT 1" % self.tableName)
		if len(result) > 0:
			return int(result[0][0])
		else:
			return 0

	def getBlockTimestamp(self, height):
		result = self.db.queryReturnAll("SELECT timestamp FROM %s ORDER BY height DESC LIMIT 1" % self.tableName)
		if len(result) > 0:
			return result[0][0]
		else:
			return 0

	def storeBlock(self, block):
		columnsText = ", ".join([column for column in self.columns])
		valuesText = ", ".join(["%s" for i in xrange(len(self.columns))])
		blockData = tuple()
		for column in self.columns:
			blockData += (block[column],)
		self.db.queryNoReturnCommit("INSERT INTO blocks_" + self.ticker + " (" + columnsText + ") VALUES (" + valuesText + ")", blockData)

	def getBlocksRange(self, offset, count):
		return self.db.queryReturnAll("SELECT timestamp, txVolume, txCount, generatedCoins, fees FROM " + self.tableName + " ORDER BY HEIGHT ASC LIMIT %s OFFSET %s", 
			(count, offset))


class PostgresPriceStorageAccess(IPriceStorageAccess):

	def __init__(self, ticker, db):
		self.db = db
		self.ticker = ticker
		self.tableName = "priceUsd_" + ticker

		self.db.queryNoReturnCommit("CREATE TABLE IF NOT EXISTS %s (timestamp TIMESTAMP PRIMARY KEY, price NUMERIC, marketcap NUMERIC, totalExchangeVolume NUMERIC)" % self.tableName)

	def storePrices(self, tuples):
		for row in tuples:
			self.db.queryNoReturnNoCommit("INSERT INTO " + self.tableName + " (timestamp, price, marketcap, totalExchangeVolume) VALUES (%s, %s, %s, %s)", row)
		self.db.commit()

	def getPrices(self):
		return self.db.queryReturnAll("SELECT timestamp, price, marketCap, totalExchangeVolume FROM " + self.tableName)

	def flushPrices(self):
		self.db.queryNoReturnCommit("TRUNCATE TABLE " + self.tableName)
