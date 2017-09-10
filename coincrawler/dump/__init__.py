from datetime import timedelta, datetime
import json

def dumpDailyStatsToCSV(currency, db):
	blocksTableName = "blocks_" + currency
	blocks = db.queryReturnAll("SELECT timestamp, txVolume, txCount, generatedCoins FROM " + blocksTableName)
	pricesTableName = "priceUsd_" + currency
	prices = db.queryReturnAll("SELECT timestamp, price, marketCap, totalExchangeVolume FROM " + pricesTableName)

	txVolumeByDay = {}
	txCountByDay = {}
	generatedCoinsByDay = {}
	for block in blocks:
		blockTimestamp = block[0].replace(second=0, microsecond=0, hour=0, minute=0) + timedelta(days=1)
		intTimestamp = int((blockTimestamp - datetime(1970, 1, 1)).total_seconds())
		if not intTimestamp in txVolumeByDay:
			txVolumeByDay[intTimestamp] = 0.0
			txCountByDay[intTimestamp] = 0
			generatedCoinsByDay[intTimestamp] = 0.0
		txVolumeByDay[intTimestamp] += float(block[1])
		txCountByDay[intTimestamp] += float(block[2])
		generatedCoinsByDay[intTimestamp] += 0.0 if block[3] is None else float(block[3])

	allData = []
	for date, price, marketcap, exchangeVolume in prices:
		row = [date]
		intTimestamp = int((date - datetime(1970, 1, 1)).total_seconds())
		if intTimestamp in txVolumeByDay:
			row.append(str(txVolumeByDay[intTimestamp] * float(price)))
			row.append(str(txCountByDay[intTimestamp]))
			row.append(str(generatedCoinsByDay[intTimestamp]))
			row.append(str(float(price)))
			row.append(str(float(marketcap)))
			row.append(str(float(exchangeVolume)))
			allData.append(row)
		else:
			print "missing timestamp for %s: %s" % (currency, str(intTimestamp))
	allData = sorted(allData, key=lambda elem: elem[0])
	if currency == "eth":
		allData.pop()

	f = open("csv/%s.csv" % currency, "w")
	f.write("date,txVolume(USD),txCount,marketcap(USD),price(USD),exchangeVolume(USD),generatedCoins\n")
	for date, txVolume, txCount, generatedCoins, price, mcap, exchangeVolume in allData:
		f.write(date.strftime('%Y/%m/%d') + ",")
		f.write(",".join([str(txVolume), str(txCount), str(mcap), str(price), str(exchangeVolume), str(generatedCoins)]))
		f.write(",")
		f.write("\n")
	f.close()
	print "%s dump done" % currency

def dumpToJson(currency):
	f = open("%s.txt" % currency, "w")
	rows = db.queryReturnAll("select * from blocks_" + currency)
	for row in rows:
		transformed = [int(row[0]), int((row[1] - datetime(1970, 1, 1)).total_seconds()), float(row[2]), int(row[3]), float(row[4]), float(row[5]), float(row[6])]
		jsonRow = json.dumps(transformed)
		f.write(jsonRow)
		f.write("\n")
	f.close()

def loadFromJson(currency):
	dbHeights = db.queryReturnAll("select height from blocks_etc")
	dbHeightsSet = set()
	for height in dbHeights:
		dbHeightsSet.add(int(height[0]))

	f = open("%s.txt" % currency, "r")
	content = f.read().split("\n")
	content.pop()
	for line in content:
		jsonLine = json.loads(line)
		height = int(jsonLine[0])
		timestamp = datetime.utcfromtimestamp(int(jsonLine[1]))
		txVolume = float(jsonLine[2])
		txCount = int(jsonLine[3])
		generatedCoins = float(jsonLine[4])
		fees = float(jsonLine[5])
		difficulty = float(jsonLine[6])
		if not height in dbHeightsSet:
			db.queryNoReturnNoCommit("insert into blocks_" + currency + " (height, timestamp, txVolume, txCount, generatedCoins, fees, difficulty) values (%s, %s, %s, %s, %s, %s, %s)", 
				(height, timestamp, txVolume, txCount, generatedCoins, fees, difficulty))
	db.commit()
	f.close()