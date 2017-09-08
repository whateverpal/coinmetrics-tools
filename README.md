# Coinmetrics tools

Repository for software created by coinmetrics.io team.

## Coincrawler

Coincrawler is a set of programs used for data extraction from blockchains and block explorers. Transaction volume, transaction count, fees and several other metrics are computed for each block and stored in the database. Additionaly, the suite contains utilities for grabbing price and exchange volume data, and dumping the obtained information to CSV file.

### Prerequisites 

Python 2.7, Posgtres database.
Python modules: psycopg2, bs4, python-dateutil, lmdb, requests.

### Supported cryptocurrencies

Bitcoin, Litecoin, ZCash, Dash, PIVX, Monero, Dogecoin, Decred, XEM, Ethereum, Ethereum Classic

Decred and XEM data is fetched from block explorers https://mainnet.decred.org and http://chain.nem.ninja respectively, Ethereum data can be fetched either from blockchain or https://etherchain.org.
