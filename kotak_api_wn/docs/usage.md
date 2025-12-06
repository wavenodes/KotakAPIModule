# Usage Guide

## Quick Start

### 1. Import and Initialize

```python
from kotak_api_wn import NeoAPI

# Create client with credentials
client = NeoAPI(
    consumer_key="your_consumer_key",
    consumer_secret="your_consumer_secret",
    environment="prod"  # "prod" for live, "uat" for testing
)
```

### 2. Authentication Flow

```python
# Step 1: Login with credentials (sends OTP)
login_response = client.login(
    mobilenumber="9876543210",
    password="your_password"
)
print(login_response)

# Step 2: Complete 2FA with OTP
otp = input("Enter OTP: ")
session_response = client.session_2fa(OTP=otp)
print(session_response)
```

### 3. Alternative: TOTP Login

```python
# Login with TOTP (if enabled)
totp_response = client.totp_login(
    mobile_number="9876543210",
    ucc="your_ucc",
    totp="123456"  # From authenticator app
)

# Validate with MPIN
client.totp_validate(mpin="123456")
```

## Trading Operations

### Place Order

```python
# Market Order
order = client.place_order(
    exchange_segment="NSE",      # NSE, BSE, NFO, etc.
    product="MIS",               # MIS, CNC, NRML
    price="0",                   # 0 for market orders
    order_type="MKT",            # MKT, L (limit), SL, SL-M
    quantity="10",
    validity="DAY",              # DAY, IOC
    trading_symbol="RELIANCE-EQ",
    transaction_type="B"         # B (buy), S (sell)
)
print(f"Order ID: {order.get('nOrdNo')}")

# Limit Order
limit_order = client.place_order(
    exchange_segment="NSE",
    product="CNC",
    price="2500.50",
    order_type="L",
    quantity="5",
    validity="DAY",
    trading_symbol="RELIANCE-EQ",
    transaction_type="B"
)

# Stop Loss Order
sl_order = client.place_order(
    exchange_segment="NSE",
    product="MIS",
    price="2450.00",
    order_type="SL",
    quantity="10",
    validity="DAY",
    trading_symbol="RELIANCE-EQ",
    transaction_type="S",
    trigger_price="2455.00"
)
```

### Modify Order

```python
# Modify with order ID only (fetches details automatically)
modified = client.modify_order(
    order_id="221206000012345",
    price="2510.00",
    order_type="L",
    quantity="5",
    validity="DAY"
)

# Modify with full details (faster)
modified = client.modify_order(
    order_id="221206000012345",
    price="2510.00",
    order_type="L",
    quantity="5",
    validity="DAY",
    instrument_token="11536",
    exchange_segment="NSE",
    product="CNC",
    trading_symbol="RELIANCE-EQ",
    transaction_type="B"
)
```

### Cancel Order

```python
# Cancel order
cancel_response = client.cancel_order(
    order_id="221206000012345",
    isVerify=True  # Verify status before cancelling
)
print(cancel_response)
```

## Portfolio & Positions

### Get Holdings

```python
holdings = client.holdings()
for holding in holdings.get('data', []):
    print(f"{holding['symbol']}: {holding['quantity']} @ {holding['avgPrice']}")
```

### Get Positions

```python
positions = client.positions()
for pos in positions.get('data', []):
    print(f"{pos['tradingSymbol']}: {pos['netQty']} P&L: {pos['pnl']}")
```

### Get Limits/Margins

```python
# All limits
limits = client.limits()
print(f"Available: {limits.get('data', {}).get('availablecash')}")

# Segment-specific limits
cash_limits = client.limits(segment="CASH", exchange="NSE")
```

## Order Reports

### Order Book

```python
orders = client.order_report()
for order in orders.get('data', []):
    print(f"{order['nOrdNo']}: {order['trdSym']} {order['ordSt']}")
```

### Order History

```python
history = client.order_history(order_id="221206000012345")
for event in history.get('data', []):
    print(f"{event['ordSt']} at {event['flDtTm']}")
```

### Trade Report

```python
# All trades
trades = client.trade_report()

# Trades for specific order
order_trades = client.trade_report(order_id="221206000012345")
```

## Market Data

### Search Scrip

```python
# Search by symbol
scrips = client.search_scrip(
    exchange_segment="NSE",
    symbol="RELIANCE"
)

# Search F&O
fo_scrips = client.search_scrip(
    exchange_segment="NFO",
    symbol="NIFTY",
    expiry="202312",
    option_type="CE",
    strike_price="20000"
)
```

### Get Quotes

```python
# Set up callbacks first
def on_message(message):
    print(f"Quote: {message}")

def on_error(error):
    print(f"Error: {error}")

client.on_message = on_message
client.on_error = on_error

# Get quotes
quotes = client.quotes(
    instrument_tokens=[
        {"exchange_segment": "nse_cm", "instrument_token": "11536"},
        {"exchange_segment": "nse_cm", "instrument_token": "1594"}
    ],
    quote_type="ltp"  # ltp, ohlc, market_depth, 52w, circuit_limits
)
```

## WebSocket Streaming

### Subscribe to Live Feed

```python
# Set up callbacks
def on_message(message):
    if message.get('type') == 'stock_feed':
        data = message.get('data', [])
        for tick in data:
            print(f"LTP: {tick.get('ltp')}")

def on_open():
    print("WebSocket connected!")

def on_close():
    print("WebSocket disconnected!")

def on_error(error):
    print(f"WebSocket error: {error}")

# Assign callbacks
client.on_message = on_message
client.on_open = on_open
client.on_close = on_close
client.on_error = on_error

# Subscribe to instruments
client.subscribe(
    instrument_tokens=[
        {"exchange_segment": "nse_cm", "instrument_token": "11536"},
        {"exchange_segment": "nse_cm", "instrument_token": "1594"}
    ],
    isIndex=False,
    isDepth=False
)
```

### Subscribe to Order Feed

```python
# Get real-time order updates
client.subscribe_to_orderfeed()
```

### Unsubscribe

```python
client.un_subscribe(
    instrument_tokens=[
        {"exchange_segment": "nse_cm", "instrument_token": "11536"}
    ]
)
```

## Session Management

### Reuse Session

```python
# After successful login, save session
session_data = client.reuse_session
# Store session_data securely

# Later, reuse the session
client = NeoAPI(
    environment="prod",
    reuse_session=session_data
)
# No need to login again!
```

### Logout

```python
client.logout()
```

## Error Handling

```python
try:
    order = client.place_order(...)
    
    if 'error' in order:
        print(f"Order failed: {order['error']}")
    else:
        print(f"Order placed: {order.get('nOrdNo')}")
        
except Exception as e:
    print(f"Exception: {e}")
```

## Best Practices

1. **Use orjson** - Install with `pip install orjson` for best performance
2. **Reuse sessions** - Avoid repeated login calls
3. **Batch operations** - Subscribe to multiple instruments at once
4. **Handle callbacks** - Always set up error handlers
5. **Use correct environments** - "uat" for testing, "prod" for live trading
