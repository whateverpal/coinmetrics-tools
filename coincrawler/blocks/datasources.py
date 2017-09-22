import requests
import json
from dateutil import parser as dateutilParser
from bs4 import BeautifulSoup
import re
from coincrawler.blockchain.bitcoin import BitcoinAccess
from coincrawler.blockchain.ethereum import EthereumAccess
from coincrawler.blockchain.monero import MoneroAccess
from datetime import datetime

class IDataSource(object):

	def getBlockHeight(self):
		return 0

	def getBlock(self, height):
		return None

	def getBlocks(self, heights):
		return None


class CryptoidDataSource(IDataSource):

	def __init__(self, ticker):
		self.ticker = ticker

	def getBlockHeight(self):
		r = requests.get("https://chainz.cryptoid.info/explorer/index.data.dws?coin=%s&n=1" % self.ticker, timeout=10)
		return int(json.loads(r.text)["blocks"][0]["height"]) - 10

	def getBlock(self, height):
		r = None
		retries = 0
		while r is None:
			try:
				r = requests.get("https://chainz.cryptoid.info/dash/block.dws?%s.htm" % height, timeout=10)
			except requests.exceptions.ReadTimeout as e:
				if retries > 3:
					raise e
				else:
					print "read timeout, retrying"
					retries += 1
		soup = BeautifulSoup(r.text, 'html.parser')
		td = soup.find("table", id="details").find_all("td")[0]
		trs = td.find_all("tr")
		
		dateText = trs[0].find("td").find("td").text
		m = re.search('[0-9][0-9][0-9][0-9]\-[0-9][0-9]\-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]', dateText)
		date = m.group(0)
		blockTimestamp = dateutilParser.parse(date)

		txCount = int(trs[0].find(text="Transactions").next_sibling.children.next()) - 1

		amount = trs[0].find(text="Value Out")
		valueOut = float(str(amount.next_sibling.children.next()).replace(",", "")) + float(amount.next_sibling.find("small").text)
		
		generated = trs[0].find(text="Created")
		generatedCoins = 0
		try:
			generatedCoins = float(str(generated.parent.next_sibling.children.next()).replace(",", "")) + float(generated.parent.next_sibling.find("small").text)
		except AttributeError:
			pass
		txVolume = max(0.0, valueOut - generatedCoins)

		return {"height": height, "timestamp": blockTimestamp, "txVolume": txVolume, "txCount": txCount, "generatedCoins": generatedCoins, "fees": 0.0, "difficulty": 0.0}


class NemNinjaDataSource(IDataSource):

	def getBlockHeight(self):
		return int(json.loads(requests.get("http://chain.nem.ninja/api3/blocks").text)[0]["height"]) - 40

	def getBlock(self, height):
		blockData = json.loads(requests.get("http://chain.nem.ninja/api3/block?height=%s" % height).text)
		blockTimestamp = dateutilParser.parse(blockData["timestamp"])
		txCount = blockData["tx_count"]

		txVolume = 0
		try:
			txData = json.loads(requests.get("http://chain.nem.ninja/api3/block_transactions?height=%s" % height).text)
			for transfer in txData["transfers"]:
				txVolume += transfer["amount"] / 1000000
		except ValueError:
			pass

		return {"height": height, "timestamp": blockTimestamp, "txVolume": txVolume, "txCount": txCount, "fees": 0.0}


class MainnetDecredOrgDataSource(IDataSource):

	def getBlockHeight(self):
		r =	requests.get("https://mainnet.decred.org/api/status?q=getInfo")
		return r.json()["info"]["blocks"] - 20

	def getBlock(self, height):
		r = requests.get("https://mainnet.decred.org/api/block-index/%s" % height)
		blockHash = r.json()["blockHash"]
		
		r = requests.get("https://mainnet.decred.org/api/block/%s" % blockHash)
		data = r.json()
		
		blockTimestamp = dateutilParser.parse(data['unixtime'])
		generatedCoins = data['reward']
		
		txCount = len(data['tx']) - 1
		txVolume = 0
		for txid in data['tx']:
			r = requests.get("https://mainnet.decred.org/api/tx/%s" % txid)
			if r.status_code == 404:
				print "404 CODE FOR TX %s" % txid
				continue
			txData = r.json()
			outputs = {}
			inputs = {}

			isCoinbase = False
			for inputData in txData['vin']:
				if 'coinbase' in inputData:
					isCoinbase = True
				else:
					r = requests.get("https://mainnet.decred.org/api/tx/%s" % inputData['txid'])
					key = frozenset(r.json()['vout'][inputData['vout']]['scriptPubKey']['addresses'])
					if not key in inputs:
						inputs[key] = 0
					inputs[key] += inputData['amountin']
			if isCoinbase:
				continue

			for outputData in txData['vout']:
				if 'addresses' in outputData['scriptPubKey']:
					key = frozenset(outputData['scriptPubKey']['addresses'])
					if not key in outputs:
						outputs[key] = 0
					outputs[key] += float(outputData['value'])

			for adrs in outputs.keys():
				inInputs = False
				for adr in adrs:
					for iAdrs in inputs.keys():
						if adr in iAdrs:
							inInputs = True
				if not inInputs:
					txVolume += outputs[adrs]

		return {"height": height, "timestamp": blockTimestamp, "generatedCoins": generatedCoins, "txCount": txCount, "txVolume": txVolume, "fees": 0.0, "difficulty": 0.0}


class BitcoinBlockchainDataSource(IDataSource):

	def __init__(self, host, port, user, password, prefetchCount, useLMDBCache=False, lmdbCachePath="", isPivx=False, maxPrefetchInputs=5000, dropBlocksCount=10):
		self.prefetchCount = prefetchCount
		self.blockchainAccess = BitcoinAccess(host, port, user, password, useLMDBCache, lmdbCachePath, isPivx, maxPrefetchInputs)
		self.steps = 0
		self.networkBlocksCount = self.blockchainAccess.getBlockCount() - dropBlocksCount

	def getBlockHeight(self):
		return self.networkBlocksCount

	def getBlock(self, height):
		if self.prefetchCount > 0 and self.steps % self.prefetchCount == 0:
			maxPrefetchHeight = min(self.networkBlocksCount, height + self.prefetchCount)
			amount = maxPrefetchHeight - height
			if amount > 0:
				self.blockchainAccess.prefetchBlocksInfo(height, amount)
			
		generatedCoins, fees, txVolume, txCount, difficulty, blockTime = self.blockchainAccess.getBlockInfo(height)
		txCount -= 1
		blockTimestamp = datetime.utcfromtimestamp(blockTime)

		self.steps += 1
		
		return {"height": height, "timestamp": blockTimestamp, "txVolume": txVolume, "txCount": txCount, "generatedCoins": generatedCoins, "fees": fees, "difficulty": difficulty}


class EthereumBlockchainDataSource(IDataSource):

	def __init__(self, host, port):
		self.ethereumAccess = EthereumAccess(host, port)
		self.networkBlocksCount = self.ethereumAccess.getBlockCount() - 100

	def getBlockHeight(self):
		return self.networkBlocksCount

	def getBlock(self, height):
		blockInfo = self.ethereumAccess.getBlockByHeight(height)
		blockTimestamp = datetime.utcfromtimestamp(int(blockInfo['timestamp'], base=16))
		difficulty = int(blockInfo['difficulty'], base=16)
		txVolume = 0.0
		fees = 0.0
		txCount = len(blockInfo['transactions'])

		receipts = self.ethereumAccess.bulkCall([("eth_getTransactionReceipt", [tx['hash']]) for tx in blockInfo['transactions']])

		index = 0
		for tx in blockInfo['transactions']:
			txValue = int(tx['value'], base=16) / 1000000000000000000.0
			txVolume += txValue
			gasUsed = int(receipts[index]['gasUsed'], base=16)
			gasPrice = int(tx['gasPrice'], base=16)
			fee = gasUsed * gasPrice / 1000000000000000000.0
			fees += fee
			index += 1

		generatedCoins = 5.0
		unclesCount = len(blockInfo['uncles'])
		unclesCountReward = unclesCount * 5.0 / 32
		generatedCoins += unclesCountReward
		unclesReward = 0.0
		if unclesCount > 0:
			uncles = self.ethereumAccess.bulkCall([("eth_getUncleByBlockNumberAndIndex", [hex(height), hex(i)]) for i in xrange(unclesCount)])
			numbers = [int(uncle['number'], base=16) for uncle in uncles]
			for n in numbers:
				unclesReward += 5.0 * (n + 8 - height) / 8
		generatedCoins += unclesReward

		return {"height": height, "timestamp": blockTimestamp, "txVolume": txVolume, "txCount": txCount, "generatedCoins": generatedCoins, "fees": fees, "difficulty": difficulty}


class EtherChainDataSource(IDataSource):

	def getBlockHeight(self):
		r = requests.get("https://etherchain.org/api/blocks/count", timeout=10)
		return r.json()["data"][0]["count"] - 100

	def getBlock(self, height):
		r = requests.get("https://etherchain.org/api/block/%s" % height, timeout=10)
		data = r.json()['data'][0]
		blockTimestamp = dateutilParser.parse(data['time'])
		difficulty = data['difficulty']
		generatedCoins = float(data['reward']) / 1000000000000000000
		fees = float(data['totalFee']) / 1000000000000000000
		generatedCoins -= fees

		r = requests.get("https://etherchain.org/api/block/%s/tx" % height, timeout=10)
		blockTxData = r.json()["data"]
		txCount = 0
		txVolume = 0.0
		for txData in blockTxData:
			amount = float(txData['amount']) / 1000000000000000000
			txCount += 1
			txVolume += amount

		return {"height": height, "timestamp": blockTimestamp, "difficulty": difficulty, "generatedCoins": generatedCoins, "fees": fees, "txCount": txCount, "txVolume": txVolume}


class MoneroBlockchainDataSource(IDataSource):

	def __init__(self, host, port):
		self.moneroAccess = MoneroAccess(host, port)
		self.networkBlocksCount = self.moneroAccess.getBlockCount() - 50

	def getBlockHeight(self):
		return self.networkBlocksCount

	def getBlock(self, height):
		blockHeaderJson = self.moneroAccess.getBlockHeaderByHeight(height)
		difficulty = blockHeaderJson["difficulty"]
		timestamp = blockHeaderJson["timestamp"]
		txCount = 0
		blockJson = self.moneroAccess.getBlockByHeight(height)
		txCount = len(blockJson['tx_hashes'])
		coinbase = self.moneroAccess.getCoinbaseTxSum(height, 1)
		fees = coinbase['fee_amount'] / 1000000000000.0
		generatedCoins = coinbase['emission_amount'] / 1000000000000.0
		return {"height": height, "timestamp": timestamp, "difficulty": difficulty, "generatedCoins": generatedCoins, "fees": fees, "txCount": txCount, "txVolume": 0.0}


class MoneroExplorerDataSource(IDataSource):

	def getBlockHeight(self):
		r = requests.get("https://moneroexplorer.com", timeout=10)
		soup = BeautifulSoup(r.text, 'html.parser')
		return int(soup.find_all(class_="primary table")[1].find("a").text) - 50

	def getBlock(self, height):
		r = requests.get("https://moneroexplorer.com/block/%s" % height, timeout=10)
		soup = BeautifulSoup(r.text, 'html.parser')
		txCount = int(soup.find_all("h3")[1].text.split("(")[1].split(")")[0])

		timestamp = dateutilParser.parse(soup.find(class_="primary table").find_all("td")[0].text.split("):")[1].split("(")[0])
		generatedCoins = float(soup.find(class_="primary table").find_all("tr")[1].find_all("td")[1].text.split(":")[1])
		if txCount == 0:
			fees = 0.0
		else:
			fees = float(soup.find(class_="primary table").find_all("tr")[2].find_all("td")[1].text.split(":")[1])

		return {"height": height, "timestamp": timestamp, "difficulty": 0, "generatedCoins": generatedCoins, "fees": fees, "txCount": txCount, "txVolume": 0.0}
