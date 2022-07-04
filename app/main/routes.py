from flask import render_template, redirect, url_for, request, jsonify, current_app
from app.main import bp
import json
import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from settings import nfts, coins, contracts, providers, api_keys, categories
from web3 import Web3, HTTPProvider, exceptions as w3exceptions
from web3.middleware import geth_poa_middleware
import random
import datetime


def get_balances(address):
    balances = {}
    for token in coins:
        if token not in balances:
            balances[token] = {}
        for network in coins[token]:

            if coins[token][network] == "coin":
                w3 = Web3(HTTPProvider(providers[network]))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                balance = w3.eth.get_balance(Web3.toChecksumAddress(address)) / (10 ** 18)
            elif coins[token][network] == "erc20":
                w3 = Web3(HTTPProvider(providers[network]))
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                contract = w3.eth.contract(address=Web3.toChecksumAddress(contracts[token]['address'][network]),
                                           abi=contracts[token]['abi'])
                balance = (contract.functions.balanceOf(Web3.toChecksumAddress(address)).call() / (10 ** 18))
            balances[token][network] = format(balance, '.8f').rstrip('0').rstrip('.')
    return balances


def get_nfts(address):
    ## OLD version, only onchain, manual call 1 time contract per NFT
    """
    nft_balances = {}
    w3 = Web3(HTTPProvider(providers['POLYGON']))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    contract = w3.eth.contract(address=Web3.toChecksumAddress(contracts['INVENTORY']['address']['POLYGON']),
                               abi=contracts['INVENTORY']['abi'])
    for nft in nfts:

        for category in categories:
            if category not in nft_balances:
                nft_balances[category] = {}
            for entry in categories[category]:
                if int(entry['start']) <= int(nft) <= int(entry['stop']):
                    balance = contract.functions.balanceOf(address, int(nft)).call() / (10 ** nfts[str(nft)]['decimals'])
                    if balance > 0:
                        nft_balances[category][str(nft)] = balance

    return nft_balances
    """
    nft_balances = {}
    url = f"https://polygon-mainnet.g.alchemy.com/nft/v2/demo/getNFTs/?owner={address}&contractAddresses[]={contracts['INVENTORY']['address']['POLYGON']}"
    # print(url)
    getnfts_json = requests.get(url=url).json()
    # print(json.dumps(getnfts_json))
    for nft in nfts:
        for category in categories:
            if category not in nft_balances:
                nft_balances[category] = {}
            for entry in categories[category]:
                if int(entry['start']) <= int(nft) <= int(entry['stop']):
                    for asset in getnfts_json['ownedNfts']:
                        if int(asset['id']['tokenId'], 16) == int(nft):
                            balance = int("{:.0f}".format(float(asset['balance']))) / (
                                    10 ** nfts[str(int(asset['id']["tokenId"], 16))]['decimals'])
                            if balance > 0:
                                nft_balances[category][str(nft)] = format(balance, '.8f').rstrip('0').rstrip('.')
    # print("returnedbalances", nft_balances)
    return nft_balances


def get_prices():
    prices = {
        "ethereum": {
            "coingecko_id": "ethereum",
            "prices": {
                "BTC": 0,
                "USD": 0}},
        "btc": {
            "coingecko_id": "bitcoin",
            "prices": {
                "BTC": 0,
                "USD": 0}},
        "sfl": {
            "coingecko_id": "sunflower-land",
            "prices": {
                "BTC": 0,
                "USD": 0}},
        "matic": {
            "coingecko_id": "matic-network",
            "prices": {
                "BTC": 0,
                "USD": 0}}}

    for coin in prices:
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{prices[coin]['coingecko_id']}?tickers=false&market_data=true&community_data=false&developer_data=false&sparkline=false"
            r = requests.get(url)
            for convert_to in prices[coin]['prices']:
                if convert_to == "BTC":
                    prices[coin]['prices'][convert_to] = format(
                        r.json()['market_data']['current_price'][convert_to.lower()], '.8f')
                else:
                    prices[coin]['prices'][convert_to] = format(
                        r.json()['market_data']['current_price'][convert_to.lower()], '.8f')
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            pass
    return prices


def get_aggregated_by_coin(prices, balances):
    total_balances = {
        "farm": {
            "USD": 0,
            "BTC": 0},
        "opensea": {
            "USD": 0,
            "BTC": 0}}
    for address_type in balances:
        for token in balances[address_type]:
            for network in balances[address_type][token]:
                if token.lower() == "usdt" or token.lower() == "usdc":
                    total_balances[address_type]["USD"] += float(balances[address_type][token][network])
                else:
                    # print(prices[token.lower()]['prices']['USD'], prices[token.lower()]['prices']['BTC'])
                    total_balances[address_type]["USD"] += float(balances[address_type][token][network]) * float(
                        prices[token.lower()]['prices']['USD'])
                    total_balances[address_type]["BTC"] += float(balances[address_type][token][network]) * float(
                        prices[token.lower()]['prices']['BTC'])
    return total_balances


def get_farmcontractdata():
    w3 = Web3(HTTPProvider(providers['POLYGON']))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    farm_contract = w3.eth.contract(address=Web3.toChecksumAddress(contracts['FARM']['address']['POLYGON']),
                                    abi=contracts['FARM']['abi'])
    return farm_contract.functions.totalSupply().call(), w3, farm_contract


def get_erctransfers_to(contractaddress, address):
    qry = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "alchemy_getAssetTransfers",
        "params": [
            {
                "toAddress": address,
                "contractAddresses": [
                    contractaddress
                ],
                "maxCount": "0x3E8",
                "excludeZeroValue": False,
                "category": [
                    "erc1155"
                ]
            }
        ]
    }
    r = requests.post(f"https://polygon-mainnet.g.alchemy.com/v2/{api_keys['alchemy']}", json=qry)
    return r.json()['result']['transfers']


def get_erctransfers_from(contractaddress, address):
    qry = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "alchemy_getAssetTransfers",
        "params": [
            {
                "fromAddress": address,
                "contractAddresses": [
                    contractaddress
                ],
                "maxCount": "0x3E8",
                "excludeZeroValue": False,
                "category": [
                    "erc1155"
                ]
            }
        ]
    }
    r = requests.post(f"https://polygon-mainnet.g.alchemy.com/v2/{api_keys['alchemy']}", json=qry)
    return r.json()['result']['transfers']


def transfer_sorting(categorized_txs, counterparties, transfer_list, farm_address="0xE79122b29CF95c0a6adCfd2663270ECa7818e0C5",
                     opensea_address="0xd649B7388DbAc76c7cAA04834Ca4EA3B1A12A23a"):
    w3 = Web3(HTTPProvider(providers['POLYGON']))

    def is_tx_in(tx):
        for category in categorized_txs:
            if tx in categorized_txs[category]:
                return True
    # print(transfer_list)

    for transfer in transfer_list:
        # print(transfer)
        cur_hash = str(transfer['hash'])
        if not is_tx_in(cur_hash):
            from_address = w3.toChecksumAddress(transfer['from'])
            to_address = w3.toChecksumAddress(transfer['to'])
            if (from_address == farm_address and to_address == opensea_address) or (
                    from_address == opensea_address and to_address == farm_address):
                if cur_hash not in categorized_txs['internal']:
                    categorized_txs['internal'][str(cur_hash)] = {}

                if to_address == opensea_address:
                    tx_type = "withdraw"
                if to_address == farm_address:
                    tx_type = "deposit"

                for token_turn in range(0, len(transfer['erc1155Metadata'])):
                    token_id = int(transfer['erc1155Metadata'][token_turn]['tokenId'], 16)
                    raw_amount = float(int(transfer['erc1155Metadata'][token_turn]['value'], 16))
                    block_num = int(transfer['blockNum'], 16)
                    decimals = nfts[str(token_id)]['decimals']
                    amount = raw_amount / (10 ** decimals)
                    categorized_txs['internal'][str(cur_hash)][str(token_id)] = {"type": tx_type, "amount": amount, "block_num": block_num}

            elif from_address == farm_address and to_address == "0x0000000000000000000000000000000000000000" or from_address == opensea_address and to_address == "0x0000000000000000000000000000000000000000":
                if cur_hash not in categorized_txs['burn']:
                    categorized_txs['burn'][str(cur_hash)] = {}

                for token_turn in range(0, len(transfer['erc1155Metadata'])):
                    token_id = int(transfer['erc1155Metadata'][token_turn]['tokenId'], 16)
                    raw_amount = float(int(transfer['erc1155Metadata'][token_turn]['value'], 16))
                    block_num = int(transfer['blockNum'], 16)
                    decimals = nfts[str(token_id)]['decimals']
                    amount = raw_amount / (10 ** decimals)
                    categorized_txs['burn'][str(cur_hash)][str(token_id)] = {
                        "type": "burn",
                        "amount": amount,
                        "block_num": block_num}
                    if str(token_id) not in categorized_txs['totalburned']:
                        categorized_txs['totalburned'][str(token_id)] = 0
                    categorized_txs['totalburned'][str(token_id)] += amount

            elif to_address == farm_address and from_address == "0x0000000000000000000000000000000000000000" or\
                    to_address == opensea_address and from_address == "0x0000000000000000000000000000000000000000":
                # print("LE VILIBN MAEHANCHE METADATAAAAA", transfer['erc1155Metadata'])

                if cur_hash not in categorized_txs['mint']:
                    categorized_txs['mint'][str(cur_hash)] = {}

                for token_turn in range(0, len(transfer['erc1155Metadata'])):
                    token_id = int(transfer['erc1155Metadata'][token_turn]['tokenId'], 16)
                    raw_amount = float(int(transfer['erc1155Metadata'][token_turn]['value'], 16))
                    block_num = int(transfer['blockNum'], 16)
                    decimals = nfts[str(token_id)]['decimals']
                    amount = raw_amount / (10 ** decimals)
                    categorized_txs['mint'][str(cur_hash)][str(token_id)] = {
                        "type": "mint",
                        "amount": amount, "block_num": block_num}
                    if str(token_id) not in categorized_txs['totalminted']:
                        categorized_txs['totalminted'][str(token_id)] = 0
                    categorized_txs['totalminted'][str(token_id)] += amount

            else:
                if from_address == farm_address or from_address == opensea_address:
                    tx_type = "sender"
                    counterparty = to_address
                else:
                    tx_type = "receiver"
                    counterparty = from_address

                if counterparty not in counterparties:
                    counterparties[counterparty] = {}

                if tx_type == "sender":
                    if 'received' not in counterparties[counterparty]:
                        counterparties[counterparty]['received'] = {}

                    if 'txout' not in counterparties[counterparty]:
                        counterparties[counterparty]['txout'] = 0
                    counterparties[counterparty]['txout'] += 1

                    for token_turn in range(0, len(transfer['erc1155Metadata'])):
                        token_id = int(transfer['erc1155Metadata'][token_turn]['tokenId'], 16)
                        raw_amount = float(int(transfer['erc1155Metadata'][token_turn]['value'], 16))
                        block_num = int(transfer['blockNum'], 16)
                        decimals = nfts[str(token_id)]['decimals']
                        amount = raw_amount / (10 ** decimals)
                        if str(cur_hash) not in categorized_txs['external']:
                            categorized_txs['external'][cur_hash] = {}
                        categorized_txs['external'][str(cur_hash)][str(token_id)] = {
                            "type": tx_type,
                            "amount": amount,
                            "counterparty": counterparty, "block_num": block_num}
                        if str(token_id) not in counterparties[counterparty]['received']:
                            counterparties[counterparty]['received'][str(token_id)] = []
                        counterparties[counterparty]['received'][str(token_id)].append({"tx": cur_hash, "amount": amount})
                        if 'totalreceived' not in counterparties[counterparty]:
                            counterparties[counterparty]['totalreceived'] = {}
                        if str(token_id) not in counterparties[counterparty]['totalreceived']:
                            counterparties[counterparty]['totalreceived'][str(token_id)] = 0
                        counterparties[counterparty]['totalreceived'][str(token_id)] += amount
                else:
                    if 'sent' not in counterparties[counterparty]:
                        counterparties[counterparty]['sent'] = {}

                    if 'txin' not in counterparties[counterparty]:
                        counterparties[counterparty]['txin'] = 0

                    counterparties[counterparty]['txin'] += 1

                    for token_turn in range(0, len(transfer['erc1155Metadata'])):
                        token_id = int(transfer['erc1155Metadata'][token_turn]['tokenId'], 16)
                        raw_amount = float(int(transfer['erc1155Metadata'][token_turn]['value'], 16))
                        block_num = int(transfer['blockNum'], 16)
                        decimals = nfts[str(token_id)]['decimals']
                        amount = raw_amount / (10 ** decimals)
                        if str(cur_hash) not in categorized_txs['external']:
                            categorized_txs['external'][cur_hash] = {}
                        categorized_txs['external'][str(cur_hash)][str(token_id)] = {
                            "type": tx_type,
                            "amount": amount,
                            "counterparty": counterparty, "block_num": block_num}
                        if str(token_id) not in counterparties[counterparty]['sent']:
                            counterparties[counterparty]['sent'][str(token_id)] = []
                        counterparties[counterparty]['sent'][str(token_id)].append({"tx": cur_hash, "amount": amount})
                        if 'totalsent' not in counterparties[counterparty]:
                            counterparties[counterparty]['totalsent'] = {}
                        if str(token_id) not in counterparties[counterparty]['totalsent']:
                            counterparties[counterparty]['totalsent'][str(token_id)] = 0
                        counterparties[counterparty]['totalsent'][str(token_id)] += amount

    return categorized_txs, counterparties


def get_farm_fromid(farm_id):
    w3 = Web3(HTTPProvider(providers['POLYGON']))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    farm_contract = w3.eth.contract(address=Web3.toChecksumAddress(contracts['FARM']['address']['POLYGON']),
                                    abi=contracts['FARM']['abi'])
    opensea_address = None
    farm_address = None

    with open("erc1155/farms.json", 'r') as f:
        farms = json.load(f)

    if str(farm_id) in farms['farms']:
        opensea_address = farms['farms'][str(farm_id)]['opensea_address']
        farm_address = farms['farms'][str(farm_id)]['farm_address']
    else:
        opensea_address, farm_address, farm_id = farm_contract.functions.getFarm(farm_id).call()
        farms[opensea_address] = farm_id
        farms[farm_address] = farm_id
        farms['farms'][str(farm_id)] = {
            "opensea_address": opensea_address,
            "farm_address": farm_address}
        with open("erc1155/farms.json", 'w') as f:
            f.write(json.dumps(farms))

    return opensea_address, farm_address, farm_id


def get_farm_fromaddress(address):
    with open("erc1155/farms.json", 'r') as f:
        farms = json.load(f)
    if str(address) in farms:
        farm_id = farms[str(address)]
    else:
        w3 = Web3(HTTPProvider(providers['POLYGON']))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        farm_contract = w3.eth.contract(address=Web3.toChecksumAddress(contracts['FARM']['address']['POLYGON']),
                                        abi=contracts['FARM']['abi'])
        farm_id = None
        if len(w3.eth.getCode(address)) == 0:
            try:
                farm_id = farm_contract.functions.tokenOfOwnerByIndex(address, 0).call()
            except:
                farm_id = None

        # Damned, that s a contract, let s find who minted it
        if farm_id is None:
            url = f"https://api.polygonscan.com/api?module=account&action=txlistinternal&address={address}&startblock=0&endblock=999999999&page=1&sort=asc&apikey={api_keys['polygonscan']}"
            result = requests.get(url=url).json()
            if result:
                try:
                    creation_tx = result['result'][0]['hash']
                    creation_tx_details = w3.eth.getTransaction(creation_tx)
                    minting_address = creation_tx_details['from']
                    farm_id = farm_contract.functions.tokenOfOwnerByIndex(address, 0).call()
                except:
                    farm_id = None
    if farm_id is None:
        return False, False, False
    else:
        return get_farm_fromid(farm_id)


@bp.route('/farminfo', methods=["POST", "GET"])
def render_farminfo():
    if request.method == 'GET':
        return redirect('/')

    # Init Params
    total_minted, w3, farm_contract = get_farmcontractdata()
    param = request.form['param']
    farm_address = None
    farm_id = None
    minting_info = None
    minting_block = None

    try:
        if param is None:
            pass
        elif w3.isAddress(param):
            farm_address = w3.toChecksumAddress(param)
        elif float(param).is_integer():
            if int(param) > total_minted:
                pass
            else:
                farm_id = int(param)
    except ValueError:
        pass

    if farm_address is not None:
        # Is that an address or a contract ?
        if len(w3.eth.getCode(farm_address)) == 0:
            farm_id = farm_contract.functions.tokenOfOwnerByIndex(farm_address, 0).call()
        # Damned, that s a contract, let s find who minted it
        else:
            url = f"https://api.polygonscan.com/api?module=account&action=txlistinternal&address={farm_address}&startblock=0&endblock=999999999&page=1&sort=asc&apikey={api_keys['polygonscan']}"
            result = requests.get(url=url).json()
            if result:
                creation_tx = result['result'][0]['hash']
                creation_tx_details = w3.eth.getTransaction(creation_tx)
                minting_address = creation_tx_details['from']
                minting_block = w3.eth.getBlock(creation_tx_details['blockNumber']).timestamp
                farm_id = farm_contract.functions.tokenOfOwnerByIndex(minting_address, 0).call()
                minting_info = {
                    "address": creation_tx_details['from'],
                    "block": creation_tx_details['blockNumber'],
                    "timestamp": w3.eth.getBlock(creation_tx_details['blockNumber']).timestamp}

    if farm_id is None:
        return redirect('/')

    opensea_address, farm_address, farm_id = get_farm_fromid(farm_id)

    if minting_block is None:
        url = f"https://api.polygonscan.com/api?module=account&action=txlistinternal&address={farm_address}&startblock=0&endblock=999999999&page=1&sort=asc&apikey={api_keys['polygonscan']}"
        result = requests.get(url=url).json()
        if result:
            creation_tx = result['result'][0]['hash']
            try:
                creation_tx_details = w3.eth.getTransaction(creation_tx)
                timestamp = w3.eth.getBlock(creation_tx_details['blockNumber']).timestamp
                minting_info = {
                    "address": creation_tx_details['from'],
                    "block": int(creation_tx_details['blockNumber'], base=16),
                    "timestamp": timestamp,
                    "date": datetime.datetime.fromtimestamp(timestamp),
                    tx: creation_tx}
            except:
                url = f"https://api.polygonscan.com/api?module=proxy&action=eth_getTransactionByHash&txhash={creation_tx}&apikey={api_keys['polygonscan']}"
                result = requests.get(url=url).json()
                timestamp = w3.eth.getBlock(result['result']['blockNumber']).timestamp

                minting_info = {
                    "address": result['result']['from'],
                    "block": int(result['result']['blockNumber'], base=16),
                    "timestamp": timestamp,
                    "date": datetime.datetime.fromtimestamp(timestamp),
                    "tx": creation_tx}

    balances = {}
    balances['opensea'] = get_balances(opensea_address)
    balances['farm'] = get_balances(farm_address)

    prices = get_prices()

    total_balances = get_aggregated_by_coin(prices, balances)

    url = f"https://api.opensea.io/api/v1/account/{opensea_address}"
    opensea_username = requests.get(url=url).json()
    try:
        opensea_username = opensea_username['data']['user']['username']
    except:
        opensea_username = None

    opensea_nfts = get_nfts(opensea_address)
    farm_nfts = get_nfts(farm_address)

    owned_nfts = {
        'opensea': opensea_nfts,
        'farm': farm_nfts}

    to_transfersf = get_erctransfers_to(contractaddress=contracts['INVENTORY']['address']['POLYGON'],
                                        address=farm_address)
    from_transfersf = get_erctransfers_from(contractaddress=contracts['INVENTORY']['address']['POLYGON'],
                                        address=farm_address)
    to_transfers = get_erctransfers_to(contractaddress=contracts['INVENTORY']['address']['POLYGON'],
                                       address=opensea_address)
    from_transfers = get_erctransfers_from(contractaddress=contracts['INVENTORY']['address']['POLYGON'],
                                        address=opensea_address)

    categorized_txs = {
        "mint": {},
        "burn": {},
        "internal": {},
        "external": {},
        "totalburned": {},
        "totalminted": {}}

    counterparties = {}

    categorized_txs, counterparties = transfer_sorting(categorized_txs=categorized_txs, transfer_list=to_transfersf,
                                                       farm_address=farm_address, opensea_address=opensea_address,
                                                       counterparties=counterparties)
    # print(len(categorized_txs['mint']), len(categorized_txs['burn']), len(categorized_txs['internal']),
    #       len(categorized_txs['external']))
    categorized_txs, counterparties = transfer_sorting(categorized_txs=categorized_txs, transfer_list=from_transfersf,
                                                       farm_address=farm_address, opensea_address=opensea_address,
                                                       counterparties=counterparties)
    # print(len(categorized_txs['mint']), len(categorized_txs['burn']), len(categorized_txs['internal']),
    #       len(categorized_txs['external']))
    categorized_txs, counterparties = transfer_sorting(categorized_txs=categorized_txs, transfer_list=to_transfers,
                                                       farm_address=farm_address, opensea_address=opensea_address,
                                                       counterparties=counterparties)
    # print(len(categorized_txs['mint']), len(categorized_txs['burn']), len(categorized_txs['internal']),
    #       len(categorized_txs['external']))
    categorized_txs, counterparties = transfer_sorting(categorized_txs=categorized_txs, transfer_list=from_transfers,
                                                       farm_address=farm_address, opensea_address=opensea_address,
                                                       counterparties=counterparties)
    # print(len(categorized_txs['mint']), len(categorized_txs['burn']), len(categorized_txs['internal']),
    #       len(categorized_txs['external']))

    with open("erc1155/categorized_txs.json", 'w') as f:
        f.write(json.dumps(categorized_txs))

    for address in counterparties:
        c_opensea_address, c_farm_address, c_farm_id = get_farm_fromaddress(address)

        if c_opensea_address and c_farm_address and c_farm_id:
            counterparties[address]['get_farm_fromaddress'] = True
            counterparties[address]['farm_id'] = c_farm_id
        else:
            counterparties[address]['get_farm_fromaddress'] = False
            counterparties[address]['farm_id'] = None

    return render_template('farminfo.html', farm_id=farm_id, nfts=nfts, owned_nfts=owned_nfts,
                           minted=total_minted, opensea_address=opensea_address,
                           farm_address=farm_address, prices=prices,
                           balances=balances, total_balances=total_balances,
                           minting_info=minting_info, opensea_username=opensea_username,
                           categorized_txs=categorized_txs, counterparties=counterparties)


@bp.route('/', methods=["GET"])
def render_index():
    total_minted, w3, farm_contract = get_farmcontractdata()
    # print(total_minted)

    return render_template('index.html', minted=total_minted)
