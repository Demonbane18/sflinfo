from __future__ import with_statement
import logging
import json
import requests
import re
from logging.handlers import RotatingFileHandler
from web3 import Web3, HTTPProvider, exceptions as w3exceptions
from web3.middleware import geth_poa_middleware
from secretsettings import api_keys



# LOGGER
class Logger:
    def __init__(self):
        self.log_file = "logs/sfl.log"
        self.logger_name = "SFL_logger"
        self.level = "DEBUG"
        self.backup_count = 10
        self.max_bytes = 10000000
        self.printformat = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'

    def get_log(self):
        _logger = logging.getLogger(self.logger_name)
        _logger.setLevel(self.level)
        _logger.addHandler(self._rotate_log())
        return _logger

    def _rotate_log(self):
        rh = RotatingFileHandler(self.log_file,
                                 maxBytes=self.max_bytes, backupCount=self.backup_count)
        formatter = logging.Formatter(self.printformat)
        rh.setFormatter(formatter)
        return rh

logger = Logger().get_log()

# ABI Gen
try:
    with open("abis/Farm.json") as f:
        farm_abi = json.load(f)
except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
    logger.warning('abis/Farm.json missing, attempting to get from github')
    raw_base_url = "https://raw.githubusercontent.com/sunflower-land/contracts/main/contracts/abis/Farm.json"
    try:
        farm_abi = requests.get(url=raw_base_url).json()
        with open("abis/Farm.json", 'w') as f:
            logger.info('abis/Farm.json github dl succeed, writing file.')
            f.write(json.dumps(farm_abi))
    except:
        logger.warning('abis/Farm.json fetch from github failed')

try:
    with open("abis/Inventory.json") as f:
        inventory_abi = json.load(f)
except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
    logger.warning('abis/Inventory.json missing, attempting to get from github')
    raw_base_url = "https://raw.githubusercontent.com/sunflower-land/contracts/main/contracts/abis/Inventory.json"
    try:
        inventory_abi = requests.get(url=raw_base_url).json()
        with open("abis/Inventory.json", 'w') as f:
            logger.info('abis/Inventory.json github dl succeed, writing file.')
            f.write(json.dumps(inventory_abi))
    except:
        logger.warning('abis/Inventory.json fetch from github failed')

try:
    with open("abis/erc20.json") as f:
        erc20_abi = json.load(f)
except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
    logger.error('abis/erc20.json missing')

try:
    with open('erc1155/nfts.json', 'r') as file:
        nfts = json.load(file)
except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
    logger.warning('erc1155/nfts.json missing, attempting to get from github')
    nfts = {}
    main_tree_url = "https://api.github.com/repos/sunflower-land/sunflower-land/git/trees/main?recursive=1"

    try:
        main_tree = requests.get(url=main_tree_url).json()
        for entry in main_tree['tree']:
            erc_ID = re.search('public/erc1155/(.*).json', entry['path'])
            if erc_ID is not None:
                if int(erc_ID.group(1)) > 0:
                    raw_base_url = "https://raw.githubusercontent.com/sunflower-land/sunflower-land/main/public/erc1155/"
                    cur_url = raw_base_url + erc_ID.group(1) + ".json"
                    nfts[erc_ID.group(1)] = requests.get(url=cur_url).json()
        with open("erc1155/nfts.json", 'w') as f:
            logger.info('erc1155/nfts.json regenerated from github, writing file.')
            f.write(json.dumps(nfts))
    except:
        print(f'nfts.json missing and autoget/gen from git failed')




providers = {
    "ETHEREUM": "https://rpc.ankr.com/eth",
    "POLYGON": "https://rpc.ankr.com/polygon"}

contracts = {
    "FARM":
        {
            "abi": farm_abi,
            "address": {
                "POLYGON": "0x2B4A66557A79263275826AD31a4cDDc2789334bD"}},
    "INVENTORY":
        {
            "abi": inventory_abi,
            "address": {
                "POLYGON": "0x22d5f9B75c524Fec1D6619787e582644CD4D7422"}},
    "ETHEREUM":
        {
            "abi": erc20_abi,
            "address": {
                "POLYGON": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"}},
    "USDT":
        {
            "abi": erc20_abi,
            "address": {
                "POLYGON": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "ETHEREUM": "0xdac17f958d2ee523a2206206994597c13d831ec7"}},
    "USDC":
        {
            "abi": erc20_abi,
            "address": {
                "POLYGON": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
                "ETHEREUM": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"}},
    "SFL":
        {
            "abi": erc20_abi,
            "address": {
                "POLYGON": "0xd1f9c58e33933a993a3891f8acfe05a68e1afc05"}},
    }

coins = {
    "MATIC": {
        "POLYGON": "coin"},
    "ETHEREUM": {
        "ETHEREUM": "coin",
        "POLYGON": "erc20"},
    "SFL": {
        "POLYGON": "erc20"},
    "USDT": {
        "ETHEREUM": "erc20",
        "POLYGON": "erc20"},
    "USDC": {
        "ETHEREUM": "erc20",
        "POLYGON": "erc20"}}

categories = {
    "Resources": [{
                      "start": 600,
                      "stop": 609}],
    "Seeds": [{
                  "start": 101,
                  "stop": 199}],
    "Tools": [{
                  "start": 300,
                  "stop": 399}],
    "Crops": [{
                  "start": 200,
                  "stop": 300}],
    "NFTs": [{
                 "start": 800,
                 "stop": 899}, {
                 "start": 610,
                 "stop": 699},
             {
                 "start": 400,
                 "stop": 499}],
    "Quests": [{
                   "start": 900,
                   "stop": 999}],
    "Food": [{
                 "start": 500,
                 "stop": 515}],
    "Badges": [{
                   "start": 700,
                   "stop": 799}]}

try:
    with open('erc1155/farms.json', 'r') as file:
        farms = json.load(file)
except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
    logger.warning('erc1155/farms.json missing')

    farms = {'farms': {}}

    with open("erc1155/farms.json", 'w') as f:
        logger.info('erc1155/farms.json regenerated from github, writing file.')
        f.write(json.dumps(farms))

