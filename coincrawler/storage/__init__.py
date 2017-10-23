class IStorage(object):

	def getBlockStorageAccess(self, currency, columns):
		return None

	def getPriceStorageAccess(self, currency):
		return None


class IBlockStorageAccess(object):

	def getBlockHeight(self):
		return 0

	def storeBlock(self, block):
		return

	def getBlocksRange(self, offset, count):
		return []


class IPriceStorageAccess(object):
	
	def storePrices(self, tuples):
		return

	def getPrices(self):
		return []

	def flushPrices(self):
		return