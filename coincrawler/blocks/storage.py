BLOCK_TABLE_COLUMNS = {
	"height": "INTEGER PRIMARY KEY",
	"timestamp": "TIMESTAMP",
	"txVolume": "NUMERIC",
	"txCount": "INTEGER",
	"generatedCoins": "NUMERIC",
	"fees": "NUMERIC",
	"difficulty": "NUMERIC",
}

class IStorage(object):

	def getBlockHeight(self):
		return 0

	def storeBlock(self, block):
		return


class PostgresDBStorage(IStorage):

	def __init__(self, ticker, columns, db):
		self.db = db
		self.ticker = ticker
		self.columns = columns
		self.createTable()

	def createTable(self):
		self.tableName = "blocks_" + self.ticker
		columnsText = ", ".join([column + " " + BLOCK_TABLE_COLUMNS[column] for column in self.columns])
		self.db.queryNoReturnCommit("CREATE TABLE IF NOT EXISTS %s (%s)" % (self.tableName, columnsText))

	def getBlockHeight(self):
		result = self.db.queryReturnAll("SELECT height FROM %s ORDER BY height DESC LIMIT 1" % self.tableName)
		if len(result) > 0:
			return int(result[0][0])
		else:
			return 0

	def storeBlock(self, block):
		columnsText = ", ".join([column for column in self.columns])
		valuesText = ", ".join(["%s" for i in xrange(len(self.columns))])
		blockData = tuple()
		for column in self.columns:
			blockData += (block[column],)
		self.db.queryNoReturnCommit("INSERT INTO blocks_" + self.ticker + " (" + columnsText + ") VALUES (" + valuesText + ")", blockData)

