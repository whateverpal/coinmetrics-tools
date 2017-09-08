from jsonrpc import *
import json
import requests

class MoneroAccess(JsonRpcCaller):

	def __init__(self, host, port):
		super(MoneroAccess, self).__init__(host, port, "", "", "json_rpc")

	def getBlockCount(self):
		return self.call("getblockcount")["count"]

	def getBlockByHeight(self, height):
		return json.loads(self.call("getblock", {"height": height})['json'])

	def getBlockHeaderByHeight(self, height):
		return self.call("getblockheaderbyheight", {"height": height})['block_header']

	def getTransactions(self, txHashes):
		payload = json.dumps({'txs_hashes': txHashes, "decode_as_json": True})
		response = requests.post("http://%s:%s/gettransactions" % (self.host, self.port), data=payload, headers={'content-type': 'application/json'})
		responseJson = response.json()
		if 'txs_as_json' in responseJson:
			result = response.json()['txs_as_json']
			return [json.loads(tx) for tx in result]
		else:
			return []

	def getCoinbaseTxSum(self, height, count):
		return self.call("get_coinbase_tx_sum", {"height": height, "count": count})
