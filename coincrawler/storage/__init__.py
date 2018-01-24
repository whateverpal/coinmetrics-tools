class IStorage(object):

	def getBlockStorageAccess(self, currency):
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

	def getBlockTimestamp(self, height):
		return 0


class IPriceStorageAccess(object):
	
	def storePrices(self, tuples):
		return

	def getPrices(self):
		return []

	def flushPrices(self):
		return