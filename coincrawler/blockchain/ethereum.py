from jsonrpc import *
import json
import requests

class EthereumAccess(JsonRpcCaller):

	def __init__(self, host, port):
		super(EthereumAccess, self).__init__(host, port, "", "")

	def getBlockCount(self):
		return int(self.call("eth_blockNumber"), base=16)

	def getCurrentBlock(self):
		return int(self.call("eth_syncing")['currentBlock'], base=16)

	def getBlockByHeight(self, height):
		return self.call("eth_getBlockByNumber", [hex(height), True])

	def getTransactionReceipt(self, txHash):
		return self.call("eth_getTransactionReceipt", [txHash])