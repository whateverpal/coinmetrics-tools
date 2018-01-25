# Coinmetrics tools

PLEASE NOTE: coinmetrics.io software now lives at https://github.com/coinmetrics-io/

## Coincrawler

Warning: this is a legacy tool that will be replaced by more robust systems soon.

Coincrawler is a set of programs used for data extraction from blockchains and block explorers. Transaction volume, transaction count, fees and amount of generated coins are computed for each block and stored in the database. Additionaly, the suite contains utilities for grabbing price and exchange volume data, and dumping the obtained information to CSV file.

### Prerequisites 

Python 2.7, Postgres database.
Python modules: psycopg2, bs4, python-dateutil, lmdb, requests.

### Supported cryptocurrencies

Coincrawler supports Bitcoin, Bitcoin Cash, Litecoin, Dash, PIVX, Monero, Dogecoin, Decred, XEM, Ethereum, Ethereum Classic, ZCash, Vertcoin, Verge, Bitcoin Gold, Digibyte and, probably, many other currencies based on Bitcoin or Ethereum code.

Data for all currencies, except Decred and NEM, is fetched from full nodes via RPC API. Remember to set -txindex=1 for Bitcoin and its clones/forks.

Decred and XEM data is fetched from block explorers https://mainnet.decred.org and http://chain.nem.ninja respectively.

### How to use

Please look at files in the examples folder. Coincrawler is a client-server software: postgres database hosting machine fetches data from servers on which cryptocurrency nodes run. 
