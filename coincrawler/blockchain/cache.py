from collections import deque
import lmdb
import json

class DictFIFOCache(object):

	def __init__(self):
		self.cache = {}
		self.cacheDeque = deque()

	def put(self, key, value):
		if not key in self.cache:
			self.cache[key] = value
			self.cacheDeque.append(key)
			if len(self.cacheDeque) > 6000:
				removeKey = self.cacheDeque.popleft()
				del self.cache[removeKey]
		else:
			print "Key %s already in cache. Programming error?" % key

	def get(self, key):
		return self.cache.get(key)


class LMDBCache(object):

	def __init__(self, dbPath):
		self.db = lmdb.open(dbPath, map_size=1024 * 1024 * 1024 * 32)
		print self.db.stat()

	def put(self, key, value):
		key = key.encode('ascii')
		strValue = json.dumps(value, ensure_ascii=True)
		with self.db.begin(write=True) as txn:
			txn.put(key, strValue)

	def get(self, key):
		key = key.encode('ascii')
		lmdbResult = None
		with self.db.begin() as txn:
			lmdbResult = txn.get(key)
		if lmdbResult is None:
			return None
		else:
			return json.loads(lmdbResult)


class ZeroCache(object):

	def put(self, key, value):
		return

	def get(self, key):
		return None