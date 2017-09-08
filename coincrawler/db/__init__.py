import psycopg2

class DBAccess(object):

	def __init__(self, dbName, dbUser, dbPassword):
		self.connection = psycopg2.connect("host=127.0.0.1 dbname=%s user=%s password=%s" % (dbName, dbUser, dbPassword))
		self.cursor = self.connection.cursor()
		print "DB connection established"

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
		print "DB connection terminated"

	def __del__(self):
		self.close()