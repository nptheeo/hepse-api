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
    try:
        if cached_data is None or (datetime.now() - cache_time).seconds > 60:
            cached_data = scraper.get_today_price()
            cache_time = datetime.now()
        return cached_data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return []

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_stock(symbol):
    """Get data for a specific stock"""
    try:
        symbol = symbol.upper()
        today_prices = get_stock_data()
        
        if not today_prices:
            return jsonify({"success": False, "error": "Unable to fetch stock data"}), 503
        
        stock_data = next((s for s in today_prices if s['symbol'] == symbol), None)
        
        if stock_data:
            prev_close = stock_data.get('previousDayClosePrice', 0)
            if prev_close == 0:
                change_percent = 0
            else:
                change = stock_data['closePrice'] - prev_close
                change_percent = (change / prev_close) * 100
            
            return jsonify({
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "symbol": stock_data['symbol'],
                    "companyName": stock_data.get('securityName', 'N/A'),
                    "businessDate": stock_data.get('businessDate', 'N/A'),
                    "price": {
                        "current": stock_data.get('closePrice', 0),
                        "open": stock_data.get('openPrice', 0),
                        "high": stock_data.get('highPrice', 0),
                        "low": stock_data.get('lowPrice', 0),
                        "previousClose": stock_data.get('previousDayClosePrice', 0),
                        "change": round(stock_data.get('closePrice', 0) - prev_close, 2),
                        "changePercent": round(change_percent, 2),
                        "averagePrice": stock_data.get('averageTradedPrice', 0)
                    },
                    "trading": {
                        "volume": stock_data.get('totalTradedQuantity', 0),
                        "totalTrades": stock_data.get('totalTrades', 0),
                        "turnover": stock_data.get('totalTradedValue', 0)
                    },
                    "yearRange": {
                        "high52Week": stock_data.get('fiftyTwoWeekHigh', 0),
                        "low52Week": stock_data.get('fiftyTwoWeekLow', 0)
                    },
                    "marketCap": stock_data.get('marketCapitalization', 0),
                    "lastUpdated": stock_data.get('lastUpdatedTime', 'N/A')
                }
            })
        else:
            return jsonify({
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "error": f"Stock '{symbol}' not found"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    """Get all stocks data"""
    try:
        today_prices = get_stock_data()
        
        if not today_prices:
            return jsonify({"success": False, "error": "Unable to fetch stock data"}), 503
        
        stocks = []
        for stock in today_prices:
            try:
                prev_close = stock.get('previousDayClosePrice', 0)
                if prev_close == 0:
                    change_percent = 0
                else:
                    change = stock['closePrice'] - prev_close
                    change_percent = (change / prev_close) * 100
                
                stocks.append({
                    "symbol": stock['symbol'],
                    "companyName": stock.get('securityName', 'N/A'),
                    "closePrice": stock.get('closePrice', 0),
                    "change": round(stock.get('closePrice', 0) - prev_close, 2),
                    "changePercent": round(change_percent, 2),
                    "volume": stock.get('totalTradedQuantity', 0)
                })
            except Exception as e:
                print(f"Error processing stock {stock.get('symbol', 'Unknown')}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "totalStocks": len(stocks),
            "data": stocks
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/api/gainers', methods=['GET'])
def get_gainers():
    """Get top gainers"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        today_prices = get_stock_data()
        
        if not today_prices:
            return jsonify({"success": False, "error": "Unable to fetch stock data"}), 503
        
        # Filter out stocks with zero previous close
        valid_stocks = []
        for stock in today_prices:
            try:
                if stock.get('previousDayClosePrice', 0) != 0:
                    valid_stocks.append(stock)
            except:
                continue
        
        sorted_stocks = sorted(
            valid_stocks,
            key=lambda x: ((x['closePrice'] - x['previousDayClosePrice']) / x['previousDayClosePrice']) * 100,
            reverse=True
        )[:limit]
        
        gainers = []
        for stock in sorted_stocks:
            try:
                prev_close = stock.get('previousDayClosePrice', 1)
                change = stock.get('closePrice', 0) - prev_close
                change_percent = (change / prev_close) * 100
                gainers.append({
                    "symbol": stock['symbol'],
                    "companyName": stock.get('securityName', 'N/A'),
                    "closePrice": stock.get('closePrice', 0),
                    "changePercent": round(change_percent, 2)
                })
            except Exception as e:
                print(f"Error processing stock {stock.get('symbol', 'Unknown')}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": gainers
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route('/api/losers', methods=['GET'])
def get_losers():
    """Get top losers"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        today_prices = get_stock_data()
        
        if not today_prices:
            return jsonify({"success": False, "error": "Unable to fetch stock data"}), 503
        
        # Filter out stocks with zero previous close
        valid_stocks = []
        for stock in today_prices:
            try:
                if stock.get('previousDayClosePrice', 0) != 0:
                    valid_stocks.append(stock)
            except:
                continue
        
        sorted_stocks = sorted(
            valid_stocks,
            key=lambda x: ((x['closePrice'] - x['previousDayClosePrice']) / x['previousDayClosePrice']) * 100
        )[:limit]
        
        losers = []
        for stock in sorted_stocks:
            try:
                prev_close = stock.get('previousDayClosePrice', 1)
                change = stock.get('closePrice', 0) - prev_close
                change_percent = (change / prev_close) * 100
                losers.append({
                    "symbol": stock['symbol'],
                    "companyName": stock.get('securityName', 'N/A'),
                    "closePrice": stock.get('closePrice', 0),
                    "changePercent": round(change_percent, 2)
                })
            except Exception as e:
                print(f"Error processing stock {stock.get('symbol', 'Unknown')}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": losers
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

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
