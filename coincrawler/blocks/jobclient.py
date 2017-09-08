import requests
import time
import json

class JobClient(object):

	def __init__(self, host, port, maxRetries=18, maxTimeout=12):
		self.host = host
		self.port = port
		self.maxRetries = maxRetries
		self.maxTimeout = maxTimeout

	def issueCommand(self, methodName, *args):
		retries = 0
		result = None
		while result is None:
			try:
				result = requests.get("http://%s:%s/%s" % (self.host, self.port, json.dumps({"method": methodName, "params": args})), timeout=self.maxTimeout)
			except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
				if retries < self.maxRetries:
					retries += 1
					print "failed to issue command due to connection error"
					print e
					time.sleep(10)
					continue
				else:
					print "too much retries, bailing out"
					raise e

			if result.status_code != 200:
				return None, result.text
			else:
				if type(result) == dict and "error" in result:
					return None, result["error"]
				else:
					try:
						result = result.json()
						return result, None
					except ValueError:
						print "json object cannot be decoded"
						if retries < self.maxRetries:
							result = None
							retries += 1
							time.sleep(10)
						else:
							return None, "json object cannot be decoded"