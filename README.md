# NEPSE Stock API

Live stock market data API for Nepal Stock Exchange (NEPSE).

## Features

- 📊 Real-time stock prices
- 📈 Top gainers and losers
- 💹 Complete trading information
- 🔄 Auto-caching for performance
- 🌐 CORS enabled for web apps

## API Endpoints

### Get Stock Data
```
GET /api/stock/{symbol}
```
Example: `/api/stock/NABIL`

### Get All Stocks
```
GET /api/stocks
```

### Get Top Gainers
```
GET /api/gainers?limit=10
```

### Get Top Losers
```
GET /api/losers?limit=10
```

## Response Format

```json
{
  "success": true,
  "timestamp": "2026-02-07T09:00:00",
  "data": {
    "symbol": "NABIL",
    "companyName": "Nabil Bank Limited",
    "price": {
      "current": 850.50,
      "change": 12.30,
      "changePercent": 1.47
    }
  }
}
```

## Local Development

```bash
pip install -r requirements.txt
python nepse_api.py
```

Visit: `http://localhost:5000`

## Deployment

Ready to deploy on:
- Render.com
- Railway.app
- PythonAnywhere

## Data Source

This API uses [nepse_scraper](https://github.com/polymorphisma/nepse_scraper) to fetch data from Nepal Stock Exchange.

## License

MIT License
