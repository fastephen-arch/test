#!/usr/bin/env python3
"""
Enhanced HSK/USDT Price Monitor with Lark Webhook Integration and Advanced Technical Analysis
Checks the price every 1 minute and sends updates to Lark bot webhook with comprehensive technical analysis
"""

import time
import requests
import json
from datetime import datetime, timedelta
import sys
from collections import deque
import statistics
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_hsk_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    def __init__(self, lookback_period=20):
        self.prices = deque(maxlen=lookback_period)
        self.timestamps = deque(maxlen=lookback_period)
        self.lookback_period = lookback_period

    def add_price(self, price, timestamp=None):
        """Add a new price to the historical data"""
        if timestamp is None:
            timestamp = datetime.now()
        self.prices.append(float(price))
        self.timestamps.append(timestamp)

    def calculate_sma(self, period=None):
        """Calculate Simple Moving Average"""
        if period is None:
            period = min(self.lookback_period, len(self.prices))
        
        if len(self.prices) < period:
            return None
        
        return sum(list(self.prices)[-period:]) / period

    def calculate_ema(self, period=12):
        """Calculate Exponential Moving Average"""
        if len(self.prices) < period:
            return None
        
        prices = list(self.prices)[-period:]
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

    def calculate_rsi(self, period=14):
        """Calculate Relative Strength Index"""
        if len(self.prices) < period + 1:
            return None

        gains = []
        losses = []

        for i in range(len(self.prices) - period, len(self.prices)):
            if i == 0:
                continue  # Skip first iteration
            if self.prices[i] > self.prices[i-1]:
                gains.append(self.prices[i] - self.prices[i-1])
                losses.append(0)
            else:
                losses.append(self.prices[i-1] - self.prices[i])
                gains.append(0)

        if len(gains) < period or len(losses) < period:
            return None

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def get_trend(self):
        """Determine the current trend based on recent prices"""
        if len(self.prices) < 5:
            return "数据不足"

        recent_prices = list(self.prices)[-5:]
        if len(set(recent_prices)) == 1:  # All prices are the same
            return "中性"

        if recent_prices[-1] > recent_prices[0]:  # Latest price higher than oldest in recent
            if recent_prices[-1] > recent_prices[-2]:  # Latest price increasing
                return "看涨"
            else:
                return "看涨反转"
        else:  # Latest price lower than oldest in recent
            if recent_prices[-1] < recent_prices[-2]:  # Latest price decreasing
                return "看跌"
            else:
                return "看跌反转"

    def analyze_support_resistance(self, window_size=8):
        """Analyze support and resistance levels"""
        if len(self.prices) < 5:
            return {"support": None, "resistance": None}
        
        # Calculate support (lowest) and resistance (highest) from recent prices
        recent_prices = list(self.prices)[-window_size:] if len(self.prices) >= window_size else list(self.prices)
        return {
            "support": min(recent_prices),
            "resistance": max(recent_prices)
        }

    def get_volatility(self, period=5):
        """Calculate price volatility over the specified period"""
        if len(self.prices) < period:
            return None
        
        recent_prices = list(self.prices)[-period:]
        if len(set(recent_prices)) == 1:  # All prices are the same
            return 0
        
        return statistics.stdev(recent_prices)

    def get_momentum(self, period=5):
        """Calculate momentum indicator"""
        if len(self.prices) < period:
            return None
        
        old_price = self.prices[-period]
        current_price = self.prices[-1]
        return ((current_price - old_price) / old_price) * 100

def get_kline_analysis():
    """Fetch and analyze 3-minute K-line data for the last 6 hours"""
    try:
        # Fetch 3-minute K-line data for the last 6 hours (120 data points)
        url = "https://api.gateio.ws/api/v4/spot/candlesticks"
        params = {
            "currency_pair": "HSK_USDT",
            "interval": "3m",
            "limit": 120
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        kline_data = response.json()
        
        if not kline_data:
            return "无法获取K线数据"
        
        # Extract closing prices
        closes = [float(k[2]) for k in kline_data]  # [timestamp, volume, close, high, low, open, ...]
        
        if len(closes) < 2:
            return "K线数据不足"
        
        start_price = closes[0]
        end_price = closes[-1]
        highest_price = max(closes)
        lowest_price = min(closes)
        
        # Calculate overall change
        overall_change = ((end_price - start_price) / start_price) * 100
        
        # Determine trend based on recent movement
        recent_closes = closes[-10:] if len(closes) >= 10 else closes
        if recent_closes[-1] > recent_closes[0]:
            kline_trend = "看涨"
        else:
            kline_trend = "看跌"
        
        # Identify key levels
        current_level = closes[-1]
        
        # Support and resistance based on recent data
        recent_highs = sorted([max(closes[max(0, i-5):i+1]) for i in range(len(closes))], reverse=True)[:5]
        recent_lows = sorted([min(closes[max(0, i-5):i+1]) for i in range(len(closes))],)[:5]
        
        resistance = recent_highs[0] if recent_highs else None
        support = recent_lows[0] if recent_lows else None
        
        # Calculate volatility
        volatility = statistics.stdev(closes) if len(closes) > 1 else 0
        
        analysis = f"K线分析: 趋势={kline_trend}, 波动率={volatility:.6f}"
        if support:
            analysis += f", 支撑={support:.6f}"
        if resistance:
            analysis += f", 阻力={resistance:.6f}"
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error fetching K-line data: {e}")
        return "K线数据获取失败"


def get_hsk_price():
    """Get current HSK/USDT price from Gate.io API with improved error handling"""
    try:
        url = "https://api.gateio.ws/api/v4/spot/tickers"
        params = {
            "currency_pair": "HSK_USDT",
            "_": int(time.time() * 1000)  # Cache buster
        }
        
        headers = {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (compatible; GateIO-Monitor/1.0)',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            ticker = data[0]
            return {
                "price": float(ticker['last']),
                "change_percentage": float(ticker['change_percentage']),
                "lowest_ask": float(ticker['lowest_ask']),
                "highest_bid": float(ticker['highest_bid']),
                "high_24h": float(ticker['high_24h']),
                "low_24h": float(ticker['low_24h']),
                "base_volume": float(ticker['base_volume']),
                "quote_volume": float(ticker['quote_volume'])
            }
        elif isinstance(data, list) and len(data) == 0:
            logger.info("No data returned from API for HSK_USDT")
            return None
        else:
            logger.error(f"Unexpected API response format: {type(data)}")
            return None
            
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        return None
    except requests.exceptions.Timeout:
        logger.error("Request timed out - possibly due to rate limiting or network issues")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Connection error - possibly due to network issues or API unavailability")
        return None
    except ValueError as e:
        logger.error(f"Error parsing JSON response: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching price: {e}")
        return None


def send_to_lark_webhook(price_data, tech_analysis):
    """Send price update to Lark bot webhook with comprehensive technical analysis"""
    try:
        webhook_url = "https://open.larksuite.com/open-apis/bot/v2/hook/14b58c66-87cc-4d66-ba9f-0efa5c5a1824"
        
        current_price = price_data["price"]
        change_pct = price_data["change_percentage"]
        
        # Get technical analysis data
        sma = tech_analysis.calculate_sma()
        ema = tech_analysis.calculate_ema()
        rsi = tech_analysis.calculate_rsi()
        trend = tech_analysis.get_trend()
        sup_res = tech_analysis.analyze_support_resistance()
        volatility = tech_analysis.get_volatility()
        momentum = tech_analysis.get_momentum()
        
        # Get K-line analysis
        kline_analysis_str = get_kline_analysis()
        
        # Format the message according to the required specification
        message_content = f'系统通知: 价格更新 HSK/USDT 当前为 {current_price:.6f} USDT (24h: {change_pct:+.2f}%)'
        
        # Extract K-line analysis components
        kline_trend = "未知"
        kline_volatility = "未知"
        kline_support = "未知"
        kline_resistance = "未知"
        
        if "K线分析:" in kline_analysis_str:
            parts = kline_analysis_str.replace("K线分析: ", "").split(", ")
            for part in parts:
                if "趋势=" in part:
                    kline_trend = part.split("=")[1]
                elif "波动率=" in part:
                    kline_volatility = part.split("=")[1]
                elif "支撑=" in part:
                    kline_support = part.split("=")[1]
                elif "阻力=" in part:
                    kline_resistance = part.split("=")[1]
        
        # Combine all technical analysis elements into one section
        ta_message_parts = [f'技术分析: 趋势={trend}']
        
        if sma:
            ta_message_parts.append(f'SMA={sma:.6f}')
        if ema:
            ta_message_parts.append(f'EMA={ema:.6f}')
        if rsi:
            ta_message_parts.append(f'RSI={rsi:.2f}')
        if sup_res['support']:
            ta_message_parts.append(f'支撑={sup_res["support"]:.6f}')
        if sup_res['resistance']:
            ta_message_parts.append(f'阻力={sup_res["resistance"]:.6f}')
        if volatility:
            ta_message_parts.append(f'波动率={volatility:.6f}')
        if momentum:
            ta_message_parts.append(f'动量={momentum:.2f}%')
        
        # Add K-line analysis components to the same section
        ta_message_parts.append(f'K线趋势={kline_trend}')
        ta_message_parts.append(f'K线波动率={kline_volatility}')
        if kline_support != "未知":
            ta_message_parts.append(f'K线支撑={kline_support}')
        if kline_resistance != "未知":
            ta_message_parts.append(f'K线阻力={kline_resistance}')
        
        ta_message = ', '.join(ta_message_parts)
        
        # Create interpretation based on combined analysis
        interpretation = generate_interpretation(
            current_price, trend, sma, rsi, sup_res, volatility, momentum,
            kline_trend, kline_volatility, kline_support, kline_resistance
        )
        
        # Combine all messages
        full_message = f'{message_content}\n{ta_message}\n{interpretation}'
        
        payload = {
            "msg_type": "text",
            "content": {
                "text": full_message
            }
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Successfully sent update to Lark webhook")
        logger.info(f"Message: {full_message}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending to Lark webhook: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to Lark webhook: {e}")
        return False

def generate_interpretation(current_price, trend, sma, rsi, sup_res, volatility, momentum, kline_trend, kline_volatility, kline_support, kline_resistance):
    """Generate market interpretation based on technical indicators"""
    interpretations = []
    
    # Trend analysis
    if trend != "数据不足":
        if trend in ["看涨", "看涨反转"]:
            interpretations.append(f"短期趋势: {trend}，价格可能继续上涨")
        elif trend in ["看跌", "看跌反转"]:
            interpretations.append(f"短期趋势: {trend}，价格可能继续下跌")
    
    # Price position relative to SMA
    if sma:
        if current_price > sma:
            interpretations.append(f"价格高于{int(sma*1000000)/1000000:.6f} SMA，看涨信号")
        else:
            interpretations.append(f"价格低于{int(sma*1000000)/1000000:.6f} SMA，看跌信号")
    
    # RSI analysis
    if rsi:
        if rsi > 70:
            interpretations.append(f"RSI超买({rsi:.2f})，可能出现回调")
        elif rsi < 30:
            interpretations.append(f"RSI超卖({rsi:.2f})，可能出现反弹")
        else:
            interpretations.append(f"RSI中性({rsi:.2f})，趋势稳定")
    
    # Support and resistance
    if sup_res['support'] and sup_res['resistance']:
        if current_price <= sup_res['support'] * 1.001:  # Within 0.1% of support
            interpretations.append(f"接近支撑位{sup_res['support']:.6f}，可能获得支撑")
        elif current_price >= sup_res['resistance'] * 0.999:  # Within 0.1% of resistance
            interpretations.append(f"接近阻力位{sup_res['resistance']:.6f}，可能遇到阻力")
        else:
            interpretations.append(f"价格在支撑{sup_res['support']:.6f}与阻力{sup_res['resistance']:.6f}之间运行")
    
    # Momentum analysis
    if momentum:
        if abs(momentum) > 5:  # Strong momentum
            direction = "上行" if momentum > 0 else "下行"
            interpretations.append(f"动量强劲({momentum:.2f}%)，{direction}趋势明显")
        elif abs(momentum) < 1:  # Weak momentum
            interpretations.append(f"动量较弱({momentum:.2f}%)，可能盘整")
    
    # K-line analysis
    if kline_trend != "未知":
        interpretations.append(f"K线趋势: {kline_trend} (6小时周期)")
    
    # Overall interpretation
    if not interpretations:
        interpretations.append("技术指标不足，建议观望")
    
    # Combine all interpretations
    return f"市场解读: {'；'.join(interpretations)}"


def main():
    logger.info("Starting Enhanced HSK/USDT Price Monitor with Lark Webhook Integration and Advanced Technical Analysis...")
    logger.info("Checking price every 1 minute and sending updates to Lark bot...")
    
    # Initialize technical analyzer
    tech_analyzer = TechnicalAnalyzer()
    
    while True:
        logger.info("Checking HSK/USDT price...")
        current_data = get_hsk_price()
        
        if current_data:
            current_price = current_data["price"]
            change_pct = current_data["change_percentage"]
            
            logger.info(f"Fetched price: ${current_price:.6f} (24h: {change_pct:+.2f}%)")
            
            # Add current price to technical analyzer
            tech_analyzer.add_price(current_price)
            
            # Send update to Lark webhook with technical analysis
            success = send_to_lark_webhook(current_data, tech_analyzer)
            
            if success:
                logger.info(f"Price: ${current_price:.6f}, 24h Change: {change_pct:+.2f}%")
            else:
                logger.error("Failed to send update to Lark webhook")
        else:
            logger.error("Failed to fetch price data")
        
        # Wait for 10 minutes (600 seconds)
        logger.info("Waiting 10 minutes until next check...")
        time.sleep(600)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
        sys.exit(0)