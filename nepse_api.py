import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

from flask import Flask, jsonify, request
from nepse_scraper import NepseScraper
from datetime import datetime
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

scraper = NepseScraper(verify_ssl=False)

cached_data = None
cache_time = None

def get_stock_data():
    global cached_data, cache_time
    if cached_data is None or (datetime.now() - cache_time).seconds > 60:
        cached_data = scraper.get_today_price()
        cache_time = datetime.now()
    return cached_data

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock(symbol):
    """Get data for a specific stock"""
    symbol = symbol.upper()
    today_prices = get_stock_data()

    stock_data = next((s for s in today_prices if s['symbol'] == symbol), None)

    if stock_data:
        change = stock_data['closePrice'] - stock_data['previousDayClosePrice']
        change_percent = (change / stock_data['previousDayClosePrice']) * 100

        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "symbol": stock_data['symbol'],
                "companyName": stock_data['securityName'],
                "businessDate": stock_data['businessDate'],
                "price": {
                    "current": stock_data['closePrice'],
                    "open": stock_data['openPrice'],
                    "high": stock_data['highPrice'],
                    "low": stock_data['lowPrice'],
                    "previousClose": stock_data['previousDayClosePrice'],
                    "change": round(change, 2),
                    "changePercent": round(change_percent, 2),
                    "averagePrice": stock_data['averageTradedPrice']
                },
                "trading": {
                    "volume": stock_data['totalTradedQuantity'],
                    "totalTrades": stock_data['totalTrades'],
                    "turnover": stock_data['totalTradedValue']
                },
                "yearRange": {
                    "high52Week": stock_data['fiftyTwoWeekHigh'],
                    "low52Week": stock_data['fiftyTwoWeekLow']
                },
                "marketCap": stock_data['marketCapitalization'],
                "lastUpdated": stock_data['lastUpdatedTime']
            }
        })
    else:
        return jsonify({
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "error": f"Stock '{symbol}' not found"
        }), 404

@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    """Get all stocks data"""
    today_prices = get_stock_data()

    stocks = []
    for stock in today_prices:
        change = stock['closePrice'] - stock['previousDayClosePrice']
        change_percent = (change / stock['previousDayClosePrice']) * 100

        stocks.append({
            "symbol": stock['symbol'],
            "companyName": stock['securityName'],
            "closePrice": stock['closePrice'],
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "volume": stock['totalTradedQuantity']
        })

    return jsonify({
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "totalStocks": len(stocks),
        "data": stocks
    })

@app.route('/api/gainers', methods=['GET'])
def get_gainers():
    """Get top gainers"""
    limit = request.args.get('limit', default=10, type=int)
    today_prices = get_stock_data()

    sorted_stocks = sorted(
        today_prices,
        key=lambda x: ((x['closePrice'] - x['previousDayClosePrice']) / x['previousDayClosePrice']) * 100,
        reverse=True
    )[:limit]

    gainers = []
    for stock in sorted_stocks:
        change = stock['closePrice'] - stock['previousDayClosePrice']
        change_percent = (change / stock['previousDayClosePrice']) * 100
        gainers.append({
            "symbol": stock['symbol'],
            "companyName": stock['securityName'],
            "closePrice": stock['closePrice'],
            "changePercent": round(change_percent, 2)
        })

    return jsonify({
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "data": gainers
    })

@app.route('/api/losers', methods=['GET'])
def get_losers():
    """Get top losers"""
    limit = request.args.get('limit', default=10, type=int)
    today_prices = get_stock_data()

    sorted_stocks = sorted(
        today_prices,
        key=lambda x: ((x['closePrice'] - x['previousDayClosePrice']) / x['previousDayClosePrice']) * 100
    )[:limit]

    losers = []
    for stock in sorted_stocks:
        change = stock['closePrice'] - stock['previousDayClosePrice']
        change_percent = (change / stock['previousDayClosePrice']) * 100
        losers.append({
            "symbol": stock['symbol'],
            "companyName": stock['securityName'],
            "closePrice": stock['closePrice'],
            "changePercent": round(change_percent, 2)
        })

    return jsonify({
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "data": losers
    })

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        "message": "NEPSE Stock API - Live Stock Market Data from Nepal Stock Exchange",
        "version": "1.0.0",
        "endpoints": {
            "/api/stock/<symbol>": "Get detailed data for specific stock (e.g., /api/stock/NABIL)",
            "/api/stocks": "Get all stocks with current prices",
            "/api/gainers?limit=10": "Get top gainers of the day",
            "/api/losers?limit=10": "Get top losers of the day"
        },
        "examples": [
            "/api/stock/NABIL",
            "/api/stock/CHL",
            "/api/gainers?limit=5",
            "/api/losers?limit=5",
            "/api/stocks"
        ],
        "documentation": "https://github.com/polymorphisma/nepse_scraper"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
