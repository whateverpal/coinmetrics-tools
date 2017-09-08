import requests
import json
import base64
import time

class RpcCallFailedException(Exception):
	pass

class JsonRpcCaller(object):

	def __init__(self, host, port, user, password, queryPath=""):
		self.host = host
		self.port = str(port)
		self.user = user
		self.password = password
		self.queryPath = queryPath	

	def makeRpcCall(self, headers, payload):
		retries = 0
		response = None
		while True:
			try:
				response = requests.post("http://%s:%s/%s" % (self.host, self.port, self.queryPath), headers=headers, data=payload)
				break
			except requests.exceptions.ConnectionError as e:
				print "failed to connect, retrying", e
				retries += 1
				time.sleep(10)

			if retries > 5:
				raise RpcCallFailedException()

		if response.status_code != 200:
			print "Invalid status code: %s" % response.status_code
			raise RpcCallFailedException()
		responseJson = response.json()
		if type(responseJson) != list:
		 	if "error" in responseJson and responseJson["error"] is not None:
				print "RPC call error: %s" % responseJson["error"]
				raise RpcCallFailedException()
			else:
				return responseJson["result"]
		else:
			result = []
			for subResult in responseJson:
				if "error" in subResult and subResult["error"] is not None:
					print "RPC call error: %s" % subResult["error"]
					raise RpcCallFailedException()
				else:
					result.append(subResult["result"])
			return result

	def call(self, method, params=[]):
		headers = {'content-type': 'application/json', 'Authorization': 'Basic ' + base64.b64encode("%s:%s" % (self.user, self.password))}
		payload = json.dumps({"jsonrpc": "2.0", "id": "0", "method": method, "params": params})
		return self.makeRpcCall(headers, payload)

	def bulkCall(self, methodParamsTuples):
		headers = {'content-type': 'application/json', 'Authorization': 'Basic ' + base64.b64encode("%s:%s" % (self.user, self.password))}
		payload = json.dumps([{"jsonrpc": "2.0", "id": "0", "method": method, "params": params} for method, params in methodParamsTuples])
		return self.makeRpcCall(headers, payload)	