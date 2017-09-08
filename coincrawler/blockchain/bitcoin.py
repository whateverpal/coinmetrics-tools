import json
import time
import binascii
from datetime import datetime
from cache import *
from jsonrpc import *
from coincrawler.utils import bech32

class BitcoinAccess(JsonRpcCaller):

	def __init__(self, host, port, user, password, useLMDBCache=False, lmdbCachePath="", isPivx=False):
		super(BitcoinAccess, self).__init__(host, port, user, password)
		if useLMDBCache:
			self.cache = LMDBCache(lmdbCachePath)
		else:
			self.cache = DictFIFOCache()
		self.isPivx = isPivx

	def getBlockCount(self):
		return self.call("getblockcount")

	def getBlockHash(self, blockHeight):
		return self.call("getblockhash", [blockHeight])

	def getBlockByHash(self, blockHash):
		return self.call("getblock", [blockHash])

	def getBlockByHeight(self, blockHeight):
		blockHash = self.getBlockHash(blockHeight)
		return self.getBlockByHash(blockHash)

	def getRawTransaction(self, txHash):
		return self.call("getrawtransaction", [txHash, 1])

	def getRawTransactionsEfficiently(self, txidList):
		result = []
		notInCache = {}
		numCached = 0
		numDuplicates = 0
		requestSet = set()
		for txid in txidList:
			if txid in requestSet:
				numDuplicates += 1
			requestSet.add(txid)

			cachedResult = self.cache.get(txid)
			if cachedResult is not None:
				numCached += 1
				result.append(cachedResult)
			else:
				result.append(None)
				if not txid in notInCache:
					notInCache[txid] = []
				notInCache[txid].append(len(result) - 1)

		notInCacheList = notInCache.keys()
		notInCacheResult = []
		if len(notInCacheList) > 0:
			print "not in cache count: %d / %d, found in cache: %d, duplicates: %d" % (len(notInCacheList), len(txidList), numCached, numDuplicates)
			notInCacheResult = self.bulkCall([("getrawtransaction", [txid, 1]) for txid in notInCacheList])
		for i in xrange(len(notInCacheList)):
			for key in ['hex', 'blockhash', 'version', 'confirmations', 'time', 'blocktime', 'locktime', 'txid']:
				del notInCacheResult[i][key]
			
			if 'vjoinsplit' in notInCacheResult[i]:
				for zcashMixerData in notInCacheResult[i]['vjoinsplit']:
					del zcashMixerData['ciphertexts']
					del zcashMixerData['randomSeed']
					del zcashMixerData['commitments']
					del zcashMixerData['proof']
					del zcashMixerData['macs']
					del zcashMixerData['nullifiers']
					del zcashMixerData['onetimePubKey']
					del zcashMixerData['anchor']

			for vout in notInCacheResult[i]['vout']:
				if vout['scriptPubKey']['type'] == 'witness_v0_keyhash' or vout['scriptPubKey']['type'] == 'witness_v0_scripthash':
					assert(not ('addresses' in vout['scriptPubKey']))
					rtxHex = vout['scriptPubKey']['hex']
					address = bech32.encode("bc", 0, [ord(symbol) for symbol in binascii.unhexlify(rtxHex[4:])])
					vout['scriptPubKey']['addresses'] = [address]

				if 'asm' in vout['scriptPubKey']:
					del vout['scriptPubKey']['asm']
				if 'hex' in vout['scriptPubKey']:
					del vout['scriptPubKey']['hex']
				if 'type' in vout['scriptPubKey']:
					del vout['scriptPubKey']['type']
				if 'reqSigs' in vout['scriptPubKey']:
					del vout['scriptPubKey']['reqSigs']
				if 'n' in vout['scriptPubKey']:
					del vout['n']

			for vin in notInCacheResult[i]['vin']:
				if 'scriptSig' in vin:
					del vin['scriptSig']
					del vin['sequence']

			self.cache.put(notInCacheList[i], notInCacheResult[i])

			for index in notInCache[notInCacheList[i]]:
				result[index] = notInCacheResult[i]

		return result

	def getTxInputOutputInfo(self, txInfo):
		outputInfo = {}
		outputs = txInfo['vout']
		for output in outputs:
			if 'addresses' in output['scriptPubKey']:
				key = frozenset(output['scriptPubKey']['addresses'])
				if not key in outputInfo:
					outputInfo[key] = 0
				outputInfo[key] += output['value']
		
		inputInfo = {}
		inputs = txInfo['vin']
		inputBulkData = self.getRawTransactionsEfficiently([inputTx['txid'] for inputTx in inputs])

		for i in xrange(len(inputs)):
			inputTx = inputs[i]
			inputTxInfo = inputBulkData[i]
			usedOutput = inputTxInfo['vout'][inputTx['vout']]
			key = frozenset(usedOutput['scriptPubKey']['addresses'])
			if not key in inputInfo:
				inputInfo[key] = 0
			inputInfo[key] += usedOutput['value']

		return (inputInfo, outputInfo)

	def getBlockInfo(self, blockHeight):
		block = self.getBlockByHeight(blockHeight)
		txsData = self.getRawTransactionsEfficiently([tx for tx in block['tx'][1:]])

		isPivxPoS = self.isPivx and blockHeight > 259200

		fees = 0.0
		volume = 0.0
		startIndex = 0 if not isPivxPoS else 1
		for txData in txsData[startIndex:]:
			inputInfo, outputInfo = self.getTxInputOutputInfo(txData)
			sumInputs = 0
			for amount in inputInfo.values():
				sumInputs += amount
			sumOutputs = 0
			for amount in outputInfo.values():
				sumOutputs += amount

			# ZEC
			if "vjoinsplit" in txData:
				for mixerData in txData["vjoinsplit"]:
					diff = mixerData["vpub_old"] - mixerData["vpub_new"]
					sumInputs -= diff
					if diff > 0:
						volume += abs(diff)

			fee = sumInputs - sumOutputs
			fees += fee
			
			for addresses, amount in outputInfo.iteritems():
				toSelf = False
				for address in addresses:
					for inputAdresses in inputInfo.keys():
						if address in inputAdresses:
							toSelf = True
				if not toSelf:
					volume += amount

		fees = max(0.0, fees)
		txCount = len(block['tx'])
		if not isPivxPoS:
			generatorTransaction = self.getRawTransactionsEfficiently([block['tx'][0]])[0]
			generatedCoinsAndFees = 0.0 
			for out in generatorTransaction['vout']:
				generatedCoinsAndFees += out['value']
			generatedCoins = generatedCoinsAndFees - fees
		else:
			generatedCoins = 0.0
			txCount -= 1
			stakeTransaction = self.getRawTransactionsEfficiently([block['tx'][1]])[0]
			inputInfo, outputInfo = self.getTxInputOutputInfo(stakeTransaction)
			sumInputs = 0
			for amount in inputInfo.values():
				sumInputs += amount
			sumOutputs = 0
			for amount in outputInfo.values():
				sumOutputs += amount
			generatedCoins = sumOutputs - sumInputs - fees

		return (generatedCoins, fees, volume, txCount, block['difficulty'], block['time'])

	def prefetchBlocksInfo(self, height, amount):
		blockHashes = self.bulkCall([("getblockhash", [height + i]) for i in xrange(amount)])
		blockInfo = self.bulkCall([ ("getblock", [blockHash]) for blockHash in blockHashes])

		txs = []
		for blockData in blockInfo:
			txs += [tx for tx in blockData['tx']]
		txsInfo = self.getRawTransactionsEfficiently(txs)

		inputTxsSet = set([])
		for tx in txsInfo:
			inputs = tx['vin']
			for inputTx in inputs:
				if 'txid' in inputTx:
					inputTxsSet.add(inputTx['txid'])
		inputTxs = list(inputTxsSet)

		if len(inputTxs) < 5000:
			self.getRawTransactionsEfficiently(inputTxs)
		else:
			print "Too big prefetch input set: %d inputs" % len(inputTxs)