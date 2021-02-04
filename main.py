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

def formatNumber(amount, precision=8, showSign=False):
    return "{:>{sign}{width}.{prec}f}".format(amount, sign='+' if showSign else '', width=precision + 5,prec=precision)

def addLossGainToBalance(asset, amount, isGain):
    if not asset in Balance:
        Balance[asset] = 0
    if isGain:
        Balance[asset] += amount
    else:
        Balance[asset] -= amount

def getPriceForSymbol(amount, symbol):
    if symbol in current_prices:
        price = current_prices[symbol]
        return amount * price
    
    print('Error: No pricelist for ' + symbol + ' or ' + symbol_reversed)
    raise

def getPriceForAssetPair(amount, baseAsset, quoteAsset):
    symbol = baseAsset + quoteAsset
    symbol_reversed = quoteAsset + baseAsset

    if symbol in current_prices:
        price = current_prices[symbol]
        return amount * price

    if symbol_reversed in current_prices:
        price = current_prices[symbol_reversed]
        return amount / price
    
    print('Error: No pricelist for ' + symbol + ' or ' + symbol_reversed)
    raise

def printCurrentPrice(symbol):
    if symbol in current_prices:
        print(symbol, current_prices[symbol])
    else:
        print('Error: No pricelist for ' + symbol)
        raise


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

def getBalanceAsString(old_balance, ignoreEmpty=True, alsoInEuro=False, onlyShowCurrencyThatChanged=False, alsoChangesInEur=True):
    padding = 12
    balance_as_string = ''
    balance_as_string += 'EUR values calculated with current BTCEUR@' + str(current_prices['BTCEUR'])+'€\n'
    total_in_eur = 0
    balance_diff = {}
    keys = ({**old_balance , **Balance} ).keys()
    for key in keys:
        old_balance_value = 0
        balance_value = 0
        if key in Balance:
            balance_value = Balance[key]
        if key in old_balance:
            old_balance_value = old_balance[key]
        balance_diff[key] = balance_value - old_balance_value
    
    win_loss_in_eur = 0
    for key in balance_diff:
        win_loss_in_eur += getPriceInEur(balance_diff[key], key)

    for key in Balance:
        if not onlyShowCurrencyThatChanged or onlyShowCurrencyThatChanged and (balance_diff[key] != 0):
            if not ignoreEmpty or ignoreEmpty and (Balance[key] != 0 or balance_diff[key] != 0):
                balance_as_string += '|' + key.ljust(padding) + ': ' + formatNumber(Balance[key])
                balance_in_eur = getPriceInEur(Balance[key], key)
                total_in_eur += balance_in_eur
                if alsoInEuro:
                    balance_as_string += ' (' + formatNumber(balance_in_eur,2) + '€)'
                balance_as_string += '|'
                if (key in balance_diff) and (balance_diff[key] != 0):
                    balance_as_string += formatNumber(balance_diff[key], showSign=True)
                    if alsoChangesInEur:
                        balance_as_string += ' (' + formatNumber(getPriceInEur(balance_diff[key], key), precision=2,showSign=True) + '€)'
                balance_as_string += '\n'
    balance_as_string += '\n|Gain/Loss in EUR: '.ljust(padding) + formatNumber(win_loss_in_eur, precision=2, showSign=True) + '€|'
    balance_as_string += '\n|Total in EUR: '.ljust(padding) + formatNumber(total_in_eur, precision=8, showSign=False) + '€|'
    return balance_as_string

def calculateHistoricalOrders():
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
            old_balance = Balance.copy()
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
            text += getBalanceAsString(old_balance, True, True, False) + '\n'
            text += '-----------------'+ '\n'
            output_file.write(text);
            print(text)
    output_file.close()

def printPriceWithConversions(startAmount, assetList):
    print('--------------------------------')
    print('->'.join(assetList))
    value = startAmount
    fee = 0
    for i in range(len(assetList)):
        print('Asset', assetList[i],'Value', formatNumber(value), 'Fee', formatNumber(fee))
        if i  < (len(assetList) - 1):
            value = getPriceForAssetPair(value, assetList[i], assetList[i + 1]) 
            if assetList[i + 1] != 'EUR' and assetList[i] != 'EUR':
                fee = value * 0.1 / 100  # substract fee
            else:
                fee = 0
            value -= fee
    return value
            



coinBalance = 0 #amount of coins (leave at 0 to pull from binance)
coin = 'DOGE' # will automatically pull the balance from binance if coinBalance is 0
includeLocked = True # will include balance that is currently locked in an order

#traiding courses in sell order (need to start with coin)
pairs = [
    ['DOGE', 'EUR'],
    ['DOGE', 'BTC', 'EUR'],
    ['DOGE', 'BTC', 'ETH', 'EUR']
]

if coinBalance == 0:
    coinBalance = client.get_asset_balance(coin)
coinAmount = float(coinBalance['free'])
if includeLocked:
    coinAmount += float(coinBalance['locked'])

highestValue = -1
highestIdx = -1
for idx in range(len(pairs)):
    value = printPriceWithConversions(coinAmount, pairs[idx])
    if value > highestValue:
        highestValue = value
        highestIdx = idx

if highestIdx >= 0:
    print('================')
    print('Highest pair', '->'.join(pairs[highestIdx]), formatNumber(highestValue))

