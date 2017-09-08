# Coinmetrics tools

Repository for software created by coinmetrics.io team.

## Coincrawler

Coincrawler is a set of programs used for data extraction from blockchains and block explorers. Transaction volume, transaction count, fees and several other metrics are computed for each block and stored in the database. Additionaly, the suite contains utilities for grabbing price and exchange volume data, and dumping the obtained information to CSV file.

### Prerequisites 

Python 2.7, Postgres database.
Python modules: psycopg2, bs4, python-dateutil, lmdb, requests.

### Supported cryptocurrencies

Coincrawler supports Bitcoin, Litecoin, Dash, PIVX, Monero, Dogecoin, Decred, XEM, Ethereum, Ethereum Classic, ZCash and, probably, many other currencies based on Bitcoin code.

Decred and XEM data is fetched from block explorers https://mainnet.decred.org and http://chain.nem.ninja respectively, Ethereum data can be fetched either from blockchain or https://etherchain.org.

### How to use

Please look at files in the examples folder. Coincrawler is a client-server software: postgres database hosting machine fetches data from servers on which cryptocurrency nodes run. 
