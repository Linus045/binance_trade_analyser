from datetime import datetime
from binance.client import Client

# Add Api key and secret
client = Client('CLIENT KEY', 'CLIENT SECRET')

# Set start balance
Balance = {
    'EUR' : 270,
    'BTC' : 0.00171993
}

# Add all pairs to analyse trades for
crypto_pairs_to_analyse = {
    'BTCEUR',
    'BTCBUSD',
    'ETHEUR',
    'ETHBTC',
    'ETHBUSD',
    'BNBBTC',
    'DOGEBTC',
    'LTCBTC',
    'SUSHIBTC',
    'AVAXBTC',
    'DOTBTC',
    '1INCHBTC',
    'BATBTC',
    'ENJBTC'
}

symbolToAssetsDict = {}
def setupSymbols():
    exchange_info = client.get_exchange_info()
    for symbol_info in exchange_info['symbols']:
        symbol_id = symbol_info['symbol']
        symbolToAssetsDict[symbol_id] = {
            'baseAsset' : symbol_info['baseAsset'],
            'quoteAsset' : symbol_info['quoteAsset'],
            'baseAssetPrecision': symbol_info['baseAssetPrecision'],
            'quoteAssetPrecision': symbol_info['quoteAssetPrecision']
        }

current_prices = {}
price_list = client.get_all_tickers()
for price_entry in price_list:
    symbol = price_entry['symbol']
    price = price_entry['price']
    current_prices[symbol] = float(price)

setupSymbols()

allOrders = []
for crypto_pair in crypto_pairs_to_analyse:
    allOrders += client.get_all_orders(symbol=crypto_pair, recvWindow=1000)

def getTime(elem):
    return elem['updateTime']
allOrders.sort(key=getTime)

def formatNumber(amount, precision=8):
    return "{:>#{width}.{prec}f}".format(amount, width=precision + 5,prec=precision)

def addLossGainToBalance(asset, amount, isGain):
    if not asset in Balance:
        Balance[asset] = 0
    if isGain:
        Balance[asset] += amount
    else:
        Balance[asset] -= amount

def getPriceInEur(amount, asset):
    if asset == 'EUR':
        return amount;
    if asset == 'BTC':
        return amount * current_prices['BTCEUR'];

    symbol_asset_btc = (asset + 'BTC') 
    symbol_btc_asset = ('BTC' + asset) 
    if symbol_asset_btc in current_prices:
        price = current_prices[symbol_asset_btc]
        return amount * price * current_prices['BTCEUR']
    elif symbol_btc_asset in current_prices:
        price = current_prices[symbol_btc_asset]
        return  amount / price * current_prices['BTCEUR']
    else:
        print('Error: No pricelist for ' + symbol_asset_btc + ' or ' + symbol_btc_asset)
        raise

def getBalanceAsString(ignoreEmpty=True, alsoInEuro=False):
    padding = 12
    balance_as_string = ''
    total_in_eur = 0
    for key in Balance:
        if not ignoreEmpty or ignoreEmpty and Balance[key] != 0:
            balance_as_string += '|' + key.ljust(padding) + ': ' + formatNumber(Balance[key])
            balance_in_eur = getPriceInEur(Balance[key], key)
            total_in_eur += balance_in_eur
            if alsoInEuro:
                balance_as_string += ' ( ~' + formatNumber(balance_in_eur,2) + '€) '
            balance_as_string += '|\n'
    balance_as_string += '\n|' + 'TOTAL IN EUR'.ljust(padding) + ': ' + formatNumber(total_in_eur) + '|'
    return balance_as_string


output_file = open("output.log", "w", encoding="utf-8")
output_file.write("")
output_file.close()

output_file = open("output.log", "a", encoding="utf-8")

for order in allOrders:
    if (order['status'] == 'FILLED') and (order['isWorking'] == True):
        symbol = order['symbol']
        symbolAssets = symbolToAssetsDict[symbol]
        baseAsset = symbolAssets['baseAsset']
        quoteAsset = symbolAssets['quoteAsset']
        
        base_digitPrecision = symbolAssets['baseAssetPrecision']
        quote_digitPrecision = symbolAssets['quoteAssetPrecision']

        price = float(order['price'])
        quantity = float(order['executedQty'])
        quoteQty = float(order['cummulativeQuoteQty'])

        if order['side'] == 'BUY':
                addLossGainToBalance(baseAsset, quantity, True)
                addLossGainToBalance(quoteAsset, quoteQty, False)
        elif order['side'] == 'SELL':
                addLossGainToBalance(baseAsset, quantity, False)
                addLossGainToBalance(quoteAsset, quoteQty, True)

        orderTime = datetime.utcfromtimestamp(int(order['time']) / 1000)
        orderTimeAsString = orderTime.strftime("%d/%m/%Y - %H:%M:%S")
        orderUpdateTime = datetime.utcfromtimestamp(int(order['updateTime']) / 1000)
        orderUpdateTimeAsString = orderTime.strftime("%d/%m/%Y - %H:%M:%S")

        text = '-------ORDER: ' + str(order['orderId']) + '-----' + '\n'
        text = orderTimeAsString  + ' (Updated:' + orderUpdateTimeAsString + ')'+ '\n'
        text += symbol;
        text += ' ' + order['side'] + '@' + formatNumber(price, base_digitPrecision) + '  Base Amount traded:' + str(quantity) + ' - '
        text += 'BaseAsset: ' + baseAsset + ' QuoteAsset: ' + quoteAsset
        text += ' (Quote amount received:'+ str(quoteQty) +')' + '\n'
        text += getBalanceAsString(True, True) + '\n'
        text += '-----------------'+ '\n'
        output_file.write(text);
        print(text)

output_file.close()