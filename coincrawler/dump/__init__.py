from datetime import timedelta, datetime
import json

def dumpDailyStatsToCSV(currency, storage):
	print "%s dump started" % currency
	allData = []
	txVolumeByDay = {}
	txCountByDay = {}
	generatedCoinsByDay = {}
	feesByDay = {}

	blockStorageAccess = storage.getBlockStorageAccess(currency)
	priceStorageAccess = storage.getPriceStorageAccess(currency)

	blocksTableName = "blocks_" + currency
	blocksCount = blockStorageAccess.getBlockHeight()
	print "blocks count: %d" % blocksCount
	batchSize = 1000000
	batchCount = blocksCount / batchSize + 1 if blocksCount % batchSize != 0 else blocksCount / batchSize
	for i in xrange(batchCount):
		offset = i * batchSize
		print "fetching %d blocks starting from %d" % (batchSize, offset)
		blocks = blockStorageAccess.getBlocksRange(offset, batchSize)
		print "fetched %d blocks" % len(blocks)
		for block in blocks:
			blockTimestamp = block[0].replace(second=0, microsecond=0, hour=0, minute=0)
			intTimestamp = int((blockTimestamp - datetime(1970, 1, 1)).total_seconds())
			if not intTimestamp in txVolumeByDay:
				txVolumeByDay[intTimestamp] = 0.0
				txCountByDay[intTimestamp] = 0
				generatedCoinsByDay[intTimestamp] = 0.0
				feesByDay[intTimestamp] = 0.0
			txVolumeByDay[intTimestamp] += float(block[1])
			txCountByDay[intTimestamp] += float(block[2])
			generatedCoinsByDay[intTimestamp] += 0.0 if block[3] is None else float(block[3])
			feesByDay[intTimestamp] += 0.0 if block[4] is None else float(block[4])

	prices = priceStorageAccess.getPrices()
	for date, price, marketcap, exchangeVolume in prices:
		row = [date]
		intTimestamp = int((date - datetime(1970, 1, 1)).total_seconds())
		if intTimestamp in txVolumeByDay:
			row.append(str(txVolumeByDay[intTimestamp] * float(price)))
			row.append(str(txCountByDay[intTimestamp]))
			row.append(str(generatedCoinsByDay[intTimestamp]))
			row.append(str(feesByDay[intTimestamp]))
		else:
			row.append("null")
			row.append("null")
			row.append("null")
			row.append("null")
			print "missing timestamp for %s: %s" % (currency, str(intTimestamp))
		row.append(str(float(price)))
		row.append(str(float(marketcap)))
		row.append(str(float(exchangeVolume)))

		allData.append(row)
	allData = sorted(allData, key=lambda elem: elem[0])

	f = open("csv/%s.csv" % currency, "w")
	f.write("date,txVolume(USD),txCount,marketcap(USD),price(USD),exchangeVolume(USD),generatedCoins,fees\n")
	for date, txVolume, txCount, generatedCoins, fees, price, mcap, exchangeVolume in allData:
		f.write(date.strftime('%Y-%m-%d') + ",")
		f.write(",".join([str(txVolume), str(txCount), str(mcap), str(price), str(exchangeVolume), str(generatedCoins), str(fees)]))
		f.write(",")
		f.write("\n")
	f.close()
	print "%s dump done" % currency