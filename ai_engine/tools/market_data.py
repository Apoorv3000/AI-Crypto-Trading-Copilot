"""Market data tool - fetch real price and volume data.

Uses CoinGecko API (free, no auth) for historical market data.
Falls back to Hyperliquid mock data if API unavailable.
"""

from typing import List, Tuple
import requests
from ai_engine.integrations.hyperliquid import HyperliquidClient


def get_market_data(
    symbol: str,
    days: int = 7
) -> Tuple[List[float], List[float]]:
    """Get historical price and volume data for a trading symbol.
    
    Uses CoinGecko API for real market data, falls back to mocks if unavailable.
    
    Args:
        symbol: Trading symbol (e.g., "ETH", "BTC")
        days: Number of days of historical data (max 365 for free tier)
        
    Returns:
        Tuple of (prices, volumes) as lists of floats
    """
    # Map symbol to CoinGecko ID
    symbol_map = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "BNB": "binancecoin",
        "SOL": "solana",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "MATIC": "matic-network",
        "DOT": "polkadot",
        "AVAX": "avalanche-2",
    }
    
    symbol_clean = symbol.upper().replace("USDT", "").replace("USD", "").replace("/", "")
    coin_id = symbol_map.get(symbol_clean, symbol_clean.lower())
    
    try:
        # CoinGecko market chart API - free, no auth
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": "daily" if days > 1 else "hourly"
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract prices and volumes
            prices = [float(p[1]) for p in data.get("prices", [])]
            volumes = [float(v[1]) for v in data.get("total_volumes", [])]
            
            if prices and volumes:
                print(f"✓ Fetched {len(prices)} data points for {symbol} from CoinGecko")
                return prices, volumes
        
        elif response.status_code == 429:
            print(f"⚠️ CoinGecko rate limit hit for {symbol}, using fallback")
    
    except Exception as e:
        print(f"⚠️ CoinGecko API error for {symbol}: {e}, using fallback")
    
    # Fallback to Hyperliquid mock data
    print(f"Using Hyperliquid mock data for {symbol}")
    client = HyperliquidClient()
    candles = client.get_candles(symbol, interval="1d", limit=days)
    
    prices = [c["close"] for c in candles]
    volumes = [c["volume"] for c in candles]
    
    return prices, volumes


def get_latest_price(symbol: str) -> float:
    """Get the latest price for a symbol.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Latest price
    """
    prices, _ = get_market_data(symbol, days=1)
    return prices[-1] if prices else 0.0
