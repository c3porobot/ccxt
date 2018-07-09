# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async.base.exchange import Exchange
from ccxt.base.errors import ExchangeError
from ccxt.base.decimal_to_precision import ROUND


class flowbtc (Exchange):

    def describe(self):
        return self.deep_extend(super(flowbtc, self).describe(), {
            'id': 'flowbtc',
            'name': 'flowBTC',
            'countries': ['BR'],  # Brazil
            'version': 'v1',
            'rateLimit': 1000,
            'has': {
                'CORS': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/28162465-cd815d4c-67cf-11e7-8e57-438bea0523a2.jpg',
                'api': 'https://api.flowbtc.com:8405/ajax',
                'www': 'https://trader.flowbtc.com',
                'doc': 'https://www.flowbtc.com.br/api.html',
            },
            'requiredCredentials': {
                'apiKey': True,
                'secret': True,
                'uid': True,
            },
            'api': {
                'public': {
                    'post': [
                        'GetTicker',
                        'GetTrades',
                        'GetTradesByDate',
                        'GetOrderBook',
                        'GetProductPairs',
                        'GetProducts',
                    ],
                },
                'private': {
                    'post': [
                        'CreateAccount',
                        'GetUserInfo',
                        'SetUserInfo',
                        'GetAccountInfo',
                        'GetAccountTrades',
                        'GetDepositAddresses',
                        'Withdraw',
                        'CreateOrder',
                        'ModifyOrder',
                        'CancelOrder',
                        'CancelAllOrders',
                        'GetAccountOpenOrders',
                        'GetOrderFee',
                    ],
                },
            },
            'fees': {
                'trading': {
                    'tierBased': False,
                    'percentage': True,
                    'maker': 0.0035,
                    'taker': 0.0035,
                },
            },
        })

    async def fetch_markets(self):
        response = await self.publicPostGetProductPairs()
        markets = response['productPairs']
        result = {}
        for p in range(0, len(markets)):
            market = markets[p]
            id = market['name']
            base = market['product1Label']
            quote = market['product2Label']
            precision = {
                'amount': self.safe_integer(market, 'product1DecimalPlaces'),
                'price': self.safe_integer(market, 'product2DecimalPlaces'),
            }
            symbol = base + '/' + quote
            result[symbol] = {
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': None,
                        'max': None,
                    },
                    'price': {
                        'min': None,
                        'max': None,
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
                'info': market,
            }
        return result

    async def fetch_balance(self, params={}):
        await self.load_markets()
        response = await self.privatePostGetAccountInfo()
        balances = response['currencies']
        result = {'info': response}
        for b in range(0, len(balances)):
            balance = balances[b]
            currency = balance['name']
            account = {
                'free': balance['balance'],
                'used': balance['hold'],
                'total': 0.0,
            }
            account['total'] = self.sum(account['free'], account['used'])
            result[currency] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        orderbook = await self.publicPostGetOrderBook(self.extend({
            'productPair': market['id'],
        }, params))
        return self.parse_order_book(orderbook, None, 'bids', 'asks', 'px', 'qty')

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        market = self.market(symbol)
        ticker = await self.publicPostGetTicker(self.extend({
            'productPair': market['id'],
        }, params))
        timestamp = self.milliseconds()
        last = self.safe_float(ticker, 'last')
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': self.safe_float(ticker, 'high'),
            'low': self.safe_float(ticker, 'low'),
            'bid': self.safe_float(ticker, 'bid'),
            'bidVolume': None,
            'ask': self.safe_float(ticker, 'ask'),
            'askVolume': None,
            'vwap': None,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': self.safe_float(ticker, 'volume24hr'),
            'quoteVolume': self.safe_float(ticker, 'volume24hrProduct2'),
            'info': ticker,
        }

    def parse_trade(self, trade, market):
        timestamp = trade['unixtime'] * 1000
        side = 'buy' if (trade['incomingOrderSide'] == 0) else 'sell'
        return {
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'id': str(trade['tid']),
            'order': None,
            'type': None,
            'side': side,
            'price': trade['px'],
            'amount': trade['qty'],
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicPostGetTrades(self.extend({
            'ins': market['id'],
            'startIndex': -1,
        }, params))
        return self.parse_trades(response['trades'], market, since, limit)

    def price_to_precision(self, symbol, price):
        return self.decimal_to_precision(price, ROUND, self.markets[symbol]['precision']['price'], self.precisionMode)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        orderType = 1 if (type == 'market') else 0
        order = {
            'ins': self.market_id(symbol),
            'side': side,
            'orderType': orderType,
            'qty': amount,
            'px': self.price_to_precision(symbol, price),
        }
        response = await self.privatePostCreateOrder(self.extend(order, params))
        return {
            'info': response,
            'id': response['serverOrderId'],
        }

    async def cancel_order(self, id, symbol=None, params={}):
        await self.load_markets()
        if 'ins' in params:
            return await self.privatePostCancelOrder(self.extend({
                'serverOrderId': id,
            }, params))
        raise ExchangeError(self.id + ' requires `ins` symbol parameter for cancelling an order')

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'] + '/' + self.version + '/' + path
        if api == 'public':
            if params:
                body = self.json(params)
        else:
            self.check_required_credentials()
            nonce = self.nonce()
            auth = str(nonce) + self.uid + self.apiKey
            signature = self.hmac(self.encode(auth), self.encode(self.secret))
            body = self.json(self.extend({
                'apiKey': self.apiKey,
                'apiNonce': nonce,
                'apiSig': signature.upper(),
            }, params))
            headers = {
                'Content-Type': 'application/json',
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    async def request(self, path, api='public', method='GET', params={}, headers=None, body=None):
        response = await self.fetch2(path, api, method, params, headers, body)
        if 'isAccepted' in response:
            if response['isAccepted']:
                return response
        raise ExchangeError(self.id + ' ' + self.json(response))
