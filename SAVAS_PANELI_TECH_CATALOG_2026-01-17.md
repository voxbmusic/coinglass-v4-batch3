Türev & Likidite (Derivatives & Liquidity Metrics)
	•	Real-time Open Interest
	•	CoinGlass API Endpoint: Yes – use GET /api/futures/open-interest/exchange-list . This returns open interest across exchanges for a given coin (BTC).
	•	API Parameters: symbol=BTC. Optionally, exchange_list=ALL to aggregate all exchanges (default is all if not specified). No interval needed for a current snapshot.
	•	Accessible in Startup Plan: Yes (✅ OK) – Open interest data is core and available on the Startup plan  .
	•	Community Workarounds: Not required since CoinGlass provides this. (In absence of API, one could sum exchange OI from individual exchange APIs or use aggregators, but CoinGlass covers it.)
	•	Alternative Free Source: If needed, use free aggregators. For example, Coinglass web (no API key) or summing Binance, CME, etc. open interest manually. No single free API for total OI exists publicly; one would combine exchange data.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/futures/open-interest/exchange-list"
headers = {"CG-API-KEY": API_KEY}
params = {"symbol": "BTC"}
data = requests.get(url, headers=headers, params=params).json()

This returns a list of exchanges with their BTC open interest. Sum their openInterest values to get total OI (in USD).

	•	Normalizer Structure: Sum the exchange OIs to get total open interest. Compute changes if needed (e.g. 1h/4h change by comparing with cached past values). For example:

def normalize_open_interest(exchange_list):
    total_oi = sum(ex['openInterest'] for ex in exchange_list)
    # Compute change vs 1h/4h ago if those values available
    return {"value": total_oi, "change_1h": ch1h, "change_4h": ch4h}

Ensure output includes current value (USD) and any relative changes (in $ and %).

	•	Adapter Module Suggestion: Use the main CoinGlass adapter (e.g. coinglass_v4.py) for this metric.

	•	Open Interest Change ($, %)
	•	CoinGlass API Endpoint: No direct endpoint for “change”; must be derived. Use the above OI endpoints (exchange-list or history) to calculate change. For example, fetch current OI and subtract OI from 1h/4h earlier. CoinGlass provides historical OI via GET /api/futures/open-interest/aggregated-history for BTC , which can be used to get earlier values.
	•	API Parameters: Use symbol=BTC, interval=1h, limit=5 (for example) on aggregated-history to get recent hourly points, or store previous snapshots from exchange-list.
	•	Accessible in Startup Plan: Yes – OI history is accessible (Startup includes open interest endpoints)  .
	•	Community Workarounds: Not needed (calculation done client-side). Communities often compute OI change from public data or CoinGlass charts.
	•	Alternative Free Source: If not using CoinGlass, one could retrieve OI from major exchange APIs (e.g. Binance, Bybit) at two timepoints and compute differences, but this is manual. No unified free source for global OI change.
	•	Python REST Example: (Using previous result data from exchange-list and cached past values)

current_total = sum(ex['openInterest'] for ex in data['data'])
past_total = get_cached_value(key="OI_total_1h_ago")
change_abs = current_total - past_total
change_pct = change_abs / past_total * 100

(Replace cache retrieval with an API call to aggregated-history if no caching.)

	•	Normalizer Structure: Calculate absolute change and percent change. E.g.:

return {"change_usd": change_abs, "change_pct": round(change_pct, 2)}

This can be merged into the open interest metric’s output.

	•	Adapter Module Suggestion: Handled in coinglass_v4.py (no separate adapter; it’s a derived metric using CoinGlass data).

	•	Weighted Funding Rate
	•	CoinGlass API Endpoint: Yes – GET /api/futures/fundingRate/oi-weight-ohlc-history (Open Interest-weighted funding rate) . This provides the OI-weighted average funding rate across exchanges (often considered the global funding rate).
	•	API Parameters: symbol=BTC, plus interval (e.g. 1h or 4h) and limit as needed. For just current value, you might use the latest data point of a 1h interval series.
	•	Accessible in Startup Plan: Yes (✅ OK) – Funding rate endpoints are included for Startup  . Weighted funding is a core metric .
	•	Community Workarounds: If CoinGlass was unavailable, a common workaround is to manually weight funding rates by OI from each exchange (data often scraped from exchange websites or using an aggregator’s free chart). However, CoinGlass provides it directly.
	•	Alternative Free Source: No direct free API for global weighted funding. One could use CryptoQuant or Glassnode if they provide a similar metric (usually paid). Alternatively, calculate from exchange data (e.g. Binance/Bybit funding and OI).
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/futures/fundingRate/oi-weight-ohlc-history"
headers = {"CG-API-KEY": API_KEY}
params = {"symbol": "BTC", "interval": "1h", "limit": 1}
resp = requests.get(url, headers=headers, params=params).json()
weighted_fr = resp['data'][-1]['close']  # last funding rate value

This yields the latest OI-weighted funding rate (e.g. in % per 8 hours).

	•	Normalizer Structure: Extract the latest funding rate value. Convert to annualized rate if needed for display (or keep per-8h rate). E.g.:

return {"value": weighted_fr, "unit": "% (8h)", "annualized": round(weighted_fr*3*365, 2)}

(Since 3 intervals of 8h per day).

	•	Adapter Module Suggestion: coinglass_v4.py (CoinGlass adapter) covers this.

	•	Long/Short Ratio (Hyperliquid / Global)
	•	CoinGlass API Endpoint: Global L/S Ratio: Yes – GET /api/futures/global-long-short-account-ratio/history  provides the global long vs short account ratio over time (across major exchanges). Hyperliquid L/S: CoinGlass has dedicated Hyperliquid endpoints (e.g. whale positions) but not a direct L/S ratio for Hyperliquid via REST in the Startup plan. The Hyperliquid L/S is likely not in the API (CoinGlass website shows it, but API is limited).
	•	API Parameters: For global ratio: symbol=BTC, optionally interval (e.g. 4h) and limit. The response gives a time series of long-short account percentage. Hyperliquid data might require specifying exchange if it were available (or could be under a Hyperliquid category if on higher plan).
	•	Accessible in Startup Plan: Global Ratio: Yes (✅ OK). Hyperliquid Ratio: Not directly – likely LOCKED or not provided in Startup. Hyperliquid metrics may require a higher tier or are not exposed via REST (marked as external in design).
	•	Community Workarounds: For Hyperliquid L/S, community members sometimes scrape the CoinGlass website or use Hyperliquid’s own API if available. If Hyperliquid exchange has a public API, one could fetch open interest long vs short from there. (Hyperliquid’s site data might be the only source; no known alternative API publicly documented).
	•	Alternative Free Source: Global L/S: Other sites like Binance’s API (for their platform’s ratio) or aggregated data on websites. But CoinGlass is unique in aggregating globally. Hyperliquid: Possibly Hyperliquid’s official API or web-scraping. If unavailable, this metric must be obtained via CoinGlass Pro or omitted.
	•	Python REST Example:

# Global long-short ratio (accounts)
url = "https://open-api-v4.coinglass.com/api/futures/global-long-short-account-ratio/history"
params = {"symbol": "BTC", "interval": "4h", "limit": 1}
ratio = requests.get(url, headers=headers, params=params).json()['data'][-1]['close']

This gives the latest global long-short account ratio (e.g. 1.5 meaning 60% long vs 40% short). Hyperliquid’s ratio would require custom handling (not available via the above).

	•	Normalizer Structure: For global, output as ratio or percentage longs vs shorts. E.g.:

return {"global_ratio": round(ratio, 2), "global_long_pct": round(100*ratio/(1+ratio),1)}

For Hyperliquid, if obtained (say via another adapter), format similarly (or as a separate field). If not available, mark as "status": "EXTERNAL_REQUIRED".

	•	Adapter Module Suggestion: Global L/S from coinglass_v4.py. Hyperliquid L/S could use a dedicated hyperliquid_public.py adapter (as planned) to fetch data from any Hyperliquid source or handle as an external metric.

	•	Liquidation Map
	•	CoinGlass API Endpoint: Yes – GET /api/futures/liquidation/map for BTC. In documentation it appears as Pair Liquidation Map and Coin Liquidation Map . The coin endpoint aggregates all futures pairs for BTC and shows liquidation levels. Use the coin-level map for an overview.
	•	API Parameters: Likely symbol=BTC. The map may not require interval (it might return current distribution of liquidation positions by price level). Possibly an exchange_list parameter if focusing on certain exchanges (default all).
	•	Accessible in Startup Plan: Yes (✅ OK) – Basic liquidation data is typically included for paid plans (CoinGlass highlights liquidation tracking). We assume Startup can access at least aggregated maps.
	•	Community Workarounds: If API is locked, traders use the CoinGlass website’s Liquidation Map or community-shared charts. No known free API alternative for aggregated liquidation levels; one could manually collect order book liquidation points from exchange APIs, but this is complex.
	•	Alternative Free Source: None directly. Some communities share liquidation heatmaps, but those are derived from CoinGlass or proprietary sources. If CoinGlass API not available, this metric might be skipped or manually interpreted from charts.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/futures/liquidation/map"
params = {"symbol": "BTC"}
resp = requests.get(url, headers=headers, params=params).json()

he response likely contains price levels and cumulative liquidation sizes at those levels. For example, it might list large liquidation clusters above/below the current price.

	•	Normalizer Structure: Parse the returned levels to identify key “liquidity walls”. For instance:

# Pseudo-code
clusters = resp['data']['clusters']
return {"largest_buy_liquidation_level": clusters['longs'][0], 
        "largest_sell_liquidation_level": clusters['shorts'][0]}

Essentially, extract significant price levels where liquidations are stacked (e.g. notable support/resistance zones). This may be output as text in the panel (e.g. “Major liquidation cluster at $X”).

	•	Adapter Module Suggestion: Use coinglass_v4.py. (No separate module needed, as CoinGlass provides this.)

	•	Liquidation Heatmap (Model 2 or 3)
	•	CoinGlass API Endpoint: Yes – CoinGlass offers multiple liquidation heatmap models. For example GET /api/futures/liquidation/heatmap/model2  or model3. Model2 is commonly used (per CoinGlass docs ). Use the coin-level heatmap for BTC.
	•	API Parameters: symbol=BTC. Possibly an exchange_list if needed (or default all exchanges). Model is chosen via the URL (model1, 2, or 3). No interval parameter – it likely returns current heatmap data (distribution of liquidation sizes across price and time).
	•	Accessible in Startup Plan: Likely Yes for basic model (✅ OK). CoinGlass highlights heatmaps as a feature , presumably accessible to Startup. If higher models (e.g. model3) are locked, use model2 which is mentioned in their guide as available.
	•	Community Workarounds: Limited. Heatmap visuals are often taken from CoinGlass UI. Without API, one might rely on screenshots or community bots posting heatmap summaries. No free API replicates this.
	•	Alternative Free Source: None widely available. This is a unique CoinGlass data visualization. If needed, one could attempt to compute a simplified version from recent liquidation events (from the “Liquidation History”) but it’s non-trivial to replicate the heatmap.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/futures/liquidation/heatmap/model2"
params = {"symbol": "BTC"}
heatmap = requests.get(url, headers=headers, params=params).json()

The JSON likely contains grids of liquidation sizes by price level. We might get data like {price: 30000, long_liq: 500BTC, short_liq: 600BTC, ...} for ranges.

	•	Normalizer Structure: Transform the heatmap into a human-readable summary. For example, identify the price with max long liquidations and max short liquidations:

max_long = max(heatmap['data'], key=lambda x: x['long_liq'])
max_short = max(heatmap['data'], key=lambda x: x['short_liq'])
return {"largest_long_liq_level": max_long['price'], 
        "long_liq_amount": max_long['long_liq'],
        "largest_short_liq_level": max_short['price'],
        "short_liq_amount": max_short['short_liq']}

This could then be formatted in text (e.g. “Biggest long liquidation pool around $30k”).

	•	Adapter Module Suggestion: Handled via coinglass_v4.py (CoinGlass adapter).

	•	Top Liquidation Events
	•	CoinGlass API Endpoint: Partial. CoinGlass has GET /api/futures/liquidation/order which returns recent liquidation orders . However, filtering “top” (largest) events must be done client-side. We can fetch recent liquidations and pick the biggest by size.
	•	API Parameters: symbol=BTC (and possibly a limit for how many recent events to fetch). If no direct symbol filter, the endpoint may return all coins and require filtering by symbol in response.
	•	Accessible in Startup Plan: Yes (✅ OK). Real-time liquidation feed is available (CoinGlass even provides WebSocket for live liquidation orders). The REST should be accessible for recent data.
	•	Community Workarounds: If not using API, communities rely on Whale alert bots or exchange liquidation feeds. Twitter accounts often post large liquidation events. But CoinGlass API is the easiest central source.
	•	Alternative Free Source: Direct exchange APIs (e.g. Bitmex, Bybit) provide liquidation feeds, but you’d need to aggregate multiple exchanges. Some free websites list recent big liquidations, but no unified API except CoinGlass or pro services.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/futures/liquidation/order"
params = {"symbol": "BTC", "limit": 50}
data = requests.get(url, headers=headers, params=params).json()
events = data['data']  # list of liquidation orders
top_events = sorted(events, key=lambda e: e['amount'], reverse=True)[:5]

This fetches recent BTC liquidation orders and then selects the top 5 by amount.

	•	Normalizer Structure: Format the top events with size and context. For example:
return [
  {"exchange": ev["exchange"], "size_usd": ev["amount_usd"], "price": ev["price"], "side": ev["side"]}
  for ev in top_events
]

The panel can list these (e.g. “Biggest liquidation: $10M long on Binance at $29,500”).

	•	Adapter Module Suggestion: coinglass_v4.py for retrieval; no special adapter needed.

	•	Orderbook Liquidity Delta
	•	CoinGlass API Endpoint: Yes – use Aggregated Orderbook Bid/Ask data. CoinGlass has GET /api/futures/orderbook/aggregated-ask-bids-history which provides total bid vs ask volumes within a price range . By choosing a narrow range (e.g. ±1% from mid-price), we can gauge the imbalance between buy and sell liquidity (the “delta”).
	•	API Parameters: symbol=BTC, exchange_list=ALL (to aggregate all exchanges), interval=h1 (1-hour granularity if historical needed) and importantly a range parameter (e.g. range=0.01 for ±1%). The Chinese documentation indicates parameters for exchange list and symbol . We set exchange_list=ALL for full market and specify the range.
	•	Accessible in Startup Plan: Likely Yes (✅ OK). Basic order book depth data should be available (the Startup plan includes ~80 endpoints, likely covering orderbook depth). If any depth endpoints are reserved, we might find it locked, but assume ±1% depth is included.
	•	Community Workarounds: Traders often look at exchange order books directly for liquidity info. A workaround is using Binance’s API for bid/ask sums at given depths and comparing. However, no free unified source across exchanges.
	•	Alternative Free Source: None aggregated. One can query top exchanges’ order books (e.g. Binance’s depth endpoint) and sum bids/asks within X% manually. This requires integration with multiple APIs.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/futures/orderbook/aggregated-ask-bids-history"
params = {"symbol": "BTC", "exchange_list": "ALL", "range": 0.01, "interval": "h1", "limit": 1}
resp = requests.get(url, headers=headers, params=params).json()
latest = resp['data'][-1]  # last hour snapshot
bids = latest['bidVolume']  # total bids within ±1%
asks = latest['askVolume']  # total asks within ±1%
delta = bids - asks

This gives total bid vs ask volume in the chosen range and their difference.

	•	Normalizer Structure: Compute the delta (bid minus ask) and perhaps a ratio. E.g.:

return {"bid_vol": bids, "ask_vol": asks, "delta": delta}


The panel might present this as, for example, “Orderbook ±1%: $X bids vs $Y asks (Δ = $Z)”, indicating whether buy or sell side is heavier.

	•	Adapter Module Suggestion: coinglass_v4.py covers this.

	•	Perpetual / Spot Volume
	•	CoinGlass API Endpoint: Yes – CoinGlass provides Futures vs Spot Volume Ratio via GET /api/index/futures-vs-spot-volume-ratio . This metric indicates the relative volume of perpetual futures vs spot markets. It might be an index value or percentage.
	•	API Parameters: Possibly none besides symbol=BTC (if needed). Likely it returns a time series or current value of the volume ratio. If not directly available as an index endpoint, one can compute from separate data: CoinGlass has total futures volume and spot volume data. For instance, using /api/futures/openInterest/History and spot volumes. But since an index exists, use that.
	•	Accessible in Startup Plan: Possibly Yes (✅ OK). It’s listed under Indicators  and likely included since it’s a high-level metric. We assume Startup access.
	•	Community Workarounds: In absence of a direct ratio, one could fetch 24h volume of BTC futures (sum across exchanges) and spot volume, then compute the ratio. This requires data from multiple sources or a site like CoinGecko for spot volume and an OI site for futures volume. CoinGlass simplifies this.
	•	Alternative Free Source: Not directly. One might approximate using CoinGecko API for BTC spot volume (global) and something like Coinglass website or CME reports for futures – but a combined ratio free is hard.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/futures-vs-spot-volume-ratio"
resp = requests.get(url, headers=headers).json()
ratio = resp['data'][-1]['value']  # assume it returns a series with 'value'

If the API is structured differently, alternatively retrieve spot and futures volumes separately and divide. For example, CoinGlass might have “Futures 24h Volume” and “Spot 24h Volume” in other endpoints.

	•	Normalizer Structure: Return the ratio (and maybe its interpretation). E.g.:
return {"ratio": round(ratio, 2)}

If ratio > 1, indicates futures volume > spot volume (leverage dominance); if < 1, spot dominates. The panel text can note this context.

	•	Adapter Module Suggestion: coinglass_v4.py.

Spot & Kurumsal (Spot & Institutional Flow Metrics)
	•	Coinbase Bitcoin Premium Index
	•	CoinGlass API Endpoint: Yes – GET /api/coinbase-premium-index . This returns the Coinbase Premium Index, i.e. the price difference (%) between BTC price on Coinbase (USD market) and Binance (USDT market) . It’s essentially U.S. vs global price spread.
	•	API Parameters: None needed for BTC – it’s specific to BTC by definition. (The endpoint may default to BTC; some sources indicate it might also support ETH with a parameter, but CoinGlass docs treat it as BTC-specific).
	•	Accessible in Startup Plan: Yes (✅ OK). This indicator is likely included (it’s commonly referenced and not marked as premium content). It’s explicitly documented, implying availability .
	•	Community Workarounds: If not via API, traders check the price on Coinbase vs Binance manually. Some use CryptoQuant’s free chart for Coinbase Premium or monitor the spread on trading terminals. Community forums often discuss this premium as an indicator of U.S. buying pressure.
	•	Alternative Free Source: CryptoQuant offers a Coinbase Premium Index chart (requires login) . Alternatively, one can query Coinbase Pro price and Binance price via their public APIs and compute the difference. For example, fetch BTC-USD price from Coinbase API and BTC-USDT price from Binance API, then compute premium = (Coinbase - Binance)/Binance * 100%. This is a straightforward fallback using exchange APIs.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/coinbase-premium-index"
premium = requests.get(url, headers=headers).json()['data']  # likely returns % premium

Suppose it returns a time series or a current value (e.g. premium = -0.5 meaning -0.5%). We can use the latest value.

	•	Normalizer Structure: Output the premium as a percentage. E.g.:
return {"premium_pct": premium}

The panel text can say “Coinbase Premium: -0.5% (Coinbase price lower than global)” or similar.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Premium Index (Korea Premium)
	•	CoinGlass API Endpoint: No direct endpoint for the general “Premium Index” between regions (CoinGlass does not list a Korea Premium in API). This metric refers to the Korean Premium (Kimchi Premium) – the price gap between Korean exchanges and global markets. It must be obtained externally.
	•	API Parameters: N/A (no CoinGlass API). We must calculate: typically defined as percentage difference between VWAP of Korean exchanges vs others . For BTC, compare e.g. Upbit KRW price vs global USD price.
	•	Accessible in Startup Plan: No – LOCKED/Not available. (CoinGlass’s Startup plan doesn’t offer this; CoinGlass itself may not have an API endpoint for it, even if their site tracks it).
	•	Community Workarounds: Yes. Community uses CryptoQuant’s “Korea Premium Index” chart   or calculates manually. For example, fetch BTC price in KRW from Upbit API and in USD from Coinbase/Binance, convert KRW to USD, then compute premium%. Reddit threads and CryptoQuant’s guide explain this indicator .
	•	Alternative Free Source: Upbit API (or Bithumb API) for BTC/KRW price, and any global price (Binance). By formula:
\text{Korea Premium (\%)} = \frac{Price_{KRW\_market} - Price_{Global}}{Price_{Global}} \times 100\%.
For instance, if BTC is 40,000,000 KRW on Upbit and $30,000 on Binance, convert 40M KRW to USD (using KRW/USD rate) and compute difference. Exchange rate can be fetched from free FX API or assume roughly 1,300 KRW/USD.
	•	Python REST Example: (Using public exchange APIs)

upbit_price = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC").json()[0]['trade_price']
binance_price = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()['price']
# Convert KRW to USD:
krw_usd = 0.00076  # example rate
upbit_price_usd = upbit_price * krw_usd
premium_pct = (upbit_price_usd - float(binance_price)) / float(binance_price) * 100

This yields the Korea premium percentage.

	•	Normalizer Structure: Return the computed premium % with a label. E.g.:

return {"premium_pct": round(premium_pct, 2)}

In text, describe it as “Korean Premium Index”. If negative, Korea price is lower than global (often not the case historically except rare arbitrage).

	•	Adapter Module Suggestion: Implement a custom adapter, e.g. premium_index.py or include in an onchain_fallback.py (though it’s market data, not on-chain). Given the architecture plan, this could go under a general coinglass_v4.py if skipping, but since it’s external, better as a small separate module or within hyperliquid_public.py (though not Hyperliquid). Perhaps create an external_premium.py to handle regional premium calculations.

	•	Spot BTC ETF Flows (USD)
	•	CoinGlass API Endpoint: Yes – GET /api/bitcoin/etf/flow-history . This returns historical capital flows (inflows/outflows) for Bitcoin spot ETFs globally. Each data point likely shows net flow over the interval. In the example, interval 1w with limit 24 gives weekly flows . For daily panel, we might use daily or weekly interval depending on context.
	•	API Parameters: interval (e.g. 1d for daily flows or 1w for weekly), limit=N (number of periods). No need for symbol since it’s specifically Bitcoin ETFs. This covers all BTC ETFs combined (US, Canada, Europe, etc).
	•	Accessible in Startup Plan: Likely Yes (✅ OK). CoinGlass touts being first with ETF data  and includes flows in their API. It’s probably accessible to Startup users as part of the ~80 endpoints.
	•	Community Workarounds: Hard to obtain free elsewhere. Without CoinGlass, one might check each ETF provider’s reports or use paid data (e.g. Bloomberg). Some community trackers (e.g. Reddit posts or ETF sponsor websites) give daily creation/redemption data for major ETFs (like Purpose in Canada). But no unified free API.
	•	Alternative Free Source: CME ETF Reports or Sponsor websites – For instance, Purpose Bitcoin ETF publishes daily AUM which can infer flows. Yahoo Finance can provide trading volume but not creation units. In absence of CoinGlass, an alternative is scraping official ETF data (not trivial for multiple funds).
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/bitcoin/etf/flow-history"
params = {"interval": "1d", "limit": 7}
data = requests.get(url, headers=headers, params=params).json()
latest_flow = data['data'][-1]  # e.g. {"date": "...", "flow": 50e6}

This might show +$50 million (inflow) on the last day, for example.

	•	Normalizer Structure: Use the latest interval’s flow. If the panel wants just the most recent daily net flow:

return {"net_flow_usd": latest_flow['flow']}

If needed, also provide cumulative inflow/outflow separately (if the API differentiates inflow vs outflow – likely it’s net). The text can say “Spot ETF Net Flow: +$50M today” for instance.

	•	Adapter Module Suggestion: coinglass_v4.py handles this (ETF endpoints).

	•	Spot BTC ETF Net Flows
	•	CoinGlass API Endpoint: Same as above. The term “Net Flows” likely is redundant with “Flows (USD)” – possibly the panel intends one to show cumulative net flow over a period vs the other showing the single-period flow. For example, “Flows (USD)” might show today’s inflow/outflow amount, and “Net Flows” could show the sum over the week or month. There isn’t a separate endpoint; we use flow-history and sum as needed.
	•	API Parameters: Same data from /api/bitcoin/etf/flow-history. To get a net over a range, fetch multiple points and aggregate. E.g. sum last 7 days for weekly net flow.
	•	Accessible in Startup Plan: Yes – covered by the ETF flow endpoint (see above).
	•	Community Workarounds: As above, one would have to accumulate data manually from multiple reports. No direct free alternative.
	•	Alternative Free Source: None directly. (Possibly compute from daily flows obtained as above).
	•	Python REST Example: (Assuming we already got data list in the previous example)


 week_net = sum(item['flow'] for item in data['data'][-7:])  # sum of last 7 days

This yields a weekly net flow. One can similarly compute monthly net, etc.

	•	Normalizer Structure: Provide an aggregate if needed. E.g.:
return {"7d_net_flow_usd": week_net}


Or simply ensure the metric displays net flow over the desired timeframe (to be decided by panel logic).

	•	Adapter Module Suggestion: Same as ETF flows above (coinglass_v4.py).

	•	Spot BTC ETF Trading Volume
	•	CoinGlass API Endpoint: Yes – likely available via GET /api/bitcoin/etf/trading-volume or included in an ETF history endpoint. The documentation mentions ETF Trading Volume in main data categories . In the API reference, possibly ETF History or ETF Detail endpoints include daily trading volume. For instance, GET /api/bitcoin/etf/history might return various fields including volume. If not, CoinGlass’s “ETF List” or detail may have it. Another approach: sum volumes of individual ETFs.
	•	API Parameters: Possibly none if using an aggregated endpoint; or if using “ETF List”, it might return each ETF’s latest volume which can be summed. The Bitcoin ETF List  likely provides a list of ETFs with data like AUM, volume, etc.
	•	Accessible in Startup Plan: Likely Yes (✅ OK). Basic ETF stats should be included. Startup has 80+ endpoints, which covers these ETF endpoints.
	•	Community Workarounds: Without CoinGlass, one could use Yahoo Finance or Bloomberg for each ETF’s volume (e.g. check daily volume of BITO, etc.) and sum them. This is manual or requires multiple API calls (Yahoo’s free API for stock quotes could retrieve volume for each ticker like $BITO, $GBTC, etc).
	•	Alternative Free Source: Yahoo Finance API (unofficial) – for example, using Python yfinance library to get trading volume of known BTC ETFs (BITO, XBTF, etc) and summing. However, this covers only public fund volumes, not all global ETFs easily.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/bitcoin/etf/list"
data = requests.get(url, headers=headers).json()
total_volume = sum(etf['volume'] for etf in data['data'])

(Hypothetical structure: each ETF in list may have a volume field for daily trading volume in USD). If not, one could retrieve ETF History for each and take the latest volume.

	•	Normalizer Structure: Sum or report the relevant volume. E.g.:

return {"total_etf_volume_usd": total_volume}

Panel might show “BTC Spot ETFs Volume: $XYZ million (24h)”.

	•	Adapter Module Suggestion: coinglass_v4.py.

Momentum (Momentum & Extremes Metrics)
	•	RSI (Relative Strength Index)
	•	CoinGlass API Endpoint: Yes – CoinGlass provides RSI values. Under Indic->Futures, there’s Coin RSI List and Pair RSI endpoints . The Coin RSI likely gives multi-timeframe RSI for BTC. We will use daily RSI(14) for momentum. Endpoint might be GET /api/index/coin-rsi or similar (exact path not given, but the presence is documented ).
	•	API Parameters: symbol=BTC, possibly interval=1d (if needing a specific timeframe RSI). If “Coin RSI List” returns several RSIs (e.g. different period lengths or timeframes) for BTC, we may need to pick the standard 14-day daily RSI. It could also return a time series of RSI values. If so, get the latest.
	•	Accessible in Startup Plan: Yes (✅ OK). Technical indicators like RSI are likely included . RSI is a basic indicator and should not be locked.
	•	Community Workarounds: Compute RSI from price data. RSI(14) on daily can be calculated if you have historical price (free from Yahoo/Coingecko). This is the usual workaround – many use TA libraries or TradingView. If CoinGlass wasn’t used, a simple Python TA library or pandas calculation on BTC price series can provide RSI.
	•	Alternative Free Source: Yahoo Finance/Coingecko + TA – get daily prices for BTC and compute RSI. Also, some free APIs (e.g. AlphaVantage) offer crypto RSI, but with limitations. Given ease of calculation, one can DIY.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/indicator/futures/coin-rsi"  # hypothetical
params = {"symbol": "BTC", "interval": "1d"}
rsi = requests.get(url, headers=headers, params=params).json()['data']['rsi_14']

(If the endpoint differs, adjust accordingly. Alternatively, use /api/spot/price/history to get prices and compute manually.)

	•	Normalizer Structure: Provide the numeric RSI value, rounded. E.g.:
return {"rsi_14d": round(rsi, 1)}

The panel can add context like “RSI 14 = 72 (overbought)” if needed.

	•	Adapter Module Suggestion: Use coinglass_v4.py if using their indicator, or implement in a local function if pulling price data (in which case the adapter might be an internal calculation rather than external source).

	•	Funding Rate History
	•	CoinGlass API Endpoint: Yes – GET /api/futures/fundingRate/ohlc-history for BTC . This gives the historical funding rates (perhaps average across exchanges) over time. We likely want recent values or a trend. The panel may display the current funding and perhaps a recent trend or extreme. The history endpoint returns a series; the latest “close” value is the current funding rate (unweighted average).
	•	API Parameters: symbol=BTC, interval=4h or 1h (depending on granularity needed), limit e.g. 30 for last 30 periods. For a daily momentum view, using 4h interval can show intraday trend.
	•	Accessible in Startup Plan: Yes (✅ OK). Funding rate endpoints are included for Startup  .
	•	Community Workarounds: If not using CoinGlass, one can pull funding rates from a major exchange (e.g. Binance’s API) as a proxy. Many people watch Binance’s funding as an indicator. Also, some free dashboards show average funding (but not via API).
	•	Alternative Free Source: Binance API – e.g. Binance endpoint for futures funding history (gives funding every 8 hours for BTCUSDT). This can substitute but only for Binance’s rate. CryptoQuant free tier shows global funding charts, but programmatic access requires subscription.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/futures/fundingRate/ohlc-history"
params = {"symbol": "BTC", "interval": "4h", "limit": 6}  # last 24h of data
data = requests.get(url, headers=headers, params=params).json()
recent_rates = [pt['close'] for pt in data['data']]
current_funding = recent_rates[-1]

This yields an array of funding rates (e.g. 8-hour rates in %).

	•	Normalizer Structure: Provide the latest funding and perhaps change. E.g.:
return {"current_funding_pct": current_funding, "prev_funding_pct": recent_rates[-2]}

The panel text might note if funding is rising or if it’s positive/negative (sign of long/short dominance).

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Volume (24h)
	•	CoinGlass API Endpoint: Yes – use GET /api/spot/coins-markets  for BTC. This returns spot market data including 24h volume. Alternatively, CoinGlass might have a dedicated volume endpoint, but the coins-markets endpoint lists key stats for each coin (price, volume, etc). We filter BTC.
	•	API Parameters: Possibly symbol=BTC or we get the full list and find BTC. (Docs mention query by coin perhaps). We want the global 24h spot volume for BTC (across exchanges). CoinGlass likely aggregates volume across tracked spot exchanges.
	•	Accessible in Startup Plan: Yes (✅ OK). Basic spot data is part of the API and should be accessible .
	•	Community Workarounds: Use a free market data API like CoinGecko or CoinMarketCap to get 24h BTC volume (they compile global spot volume). This is a common approach if CoinGlass wasn’t used. CoinGecko’s free API gives “total_volume” for BTC easily.
	•	Alternative Free Source: CoinGecko API – e.g. GET /coins/bitcoin returns total_volume in USD. CoinMarketCap API (requires a free API key) also provides volume. These are reliable fallback sources.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/spot/coins-markets"
data = requests.get(url, headers=headers).json()
btc_data = next(item for item in data['data'] if item['symbol']=="BTC")
vol_24h = btc_data['volume_24h']

Suppose volume_24h is given in USD. This yields the 24h trading volume on spot markets.

	•	Normalizer Structure: Return the volume (perhaps in millions or billions for readability). E.g.:
return {"24h_volume_usd": vol_24h}

The panel might format it like “24h Spot Volume: $XX Bn”.

	•	Adapter Module Suggestion: coinglass_v4.py (or use a fallback adapter if we choose CoinGecko – e.g. an market_data_adapter.py using CoinGecko for resilience).

	•	Volume Change %
	•	CoinGlass API Endpoint: No direct endpoint for “volume change”. Compute from two data points: current 24h volume vs previous 24h volume (i.e. volume today vs yesterday). If using CoinGlass, one can get historical volume by calling the same endpoint twice (today and yesterday) or using a price history endpoint that might include volume. CoinGlass’s spot price history may include volume data (they often do: e.g. OHLC history might come with volume for each day).
	•	API Parameters: If using OHLC: GET /api/spot/price/history with interval=1d, limit=2 for BTC could yield yesterday’s and today’s volume. Or use CoinGlass’s own previous day volume if coins-markets returns it (likely not, it’s just current stat). So better to query a historical endpoint.
	•	Accessible in Startup Plan: Yes – spot OHLC or historical data is available .
	•	Community Workarounds: Without CoinGlass, take volume from CoinGecko for two days. CoinGecko offers historical data endpoints (or just compare current 24h vs yesterday’s value from their API). Many sites also show 24h volume change percentage which can be scraped.
	•	Alternative Free Source: CoinGecko has a simple way: current volume vs a cached value from 24h earlier. Or use their /coins/bitcoin/history endpoint for yesterday’s data.
	•	Python REST Example:
# Using CoinGlass spot price history for 2 days
url = "https://open-api-v4.coinglass.com/api/spot/price/history"
params = {"symbol": "BTC", "interval": "1d", "limit": 2}
data = requests.get(url, headers=headers, params=params).json()
vol_yesterday = data['data'][0]['volume']
vol_today = data['data'][1]['volume']
change_pct = (vol_today - vol_yesterday) / vol_yesterday * 100

This calculates the percentage change in daily volume.

	•	Normalizer Structure: Return the percentage change, e.g.:
return {"volume_change_pct": round(change_pct, 1)}

Panel can display “24h Volume Change: +X%”.

	•	Adapter Module Suggestion: coinglass_v4.py (or fallback to a market data adapter if using external API).

Smart Money (Institutional & On-Chain Metrics – Weekly)
	•	CME Long/Short Report
	•	CoinGlass API Endpoint: None. CoinGlass does not offer the CFTC Commitment of Traders (CoT) report via API. This metric refers to the CME futures positions by trader category (e.g. long vs short positions of institutions, etc.). We need a fallback data source.
	•	API Parameters: N/A for CoinGlass. The data is released weekly by CFTC (every Friday for Tuesday’s positions). We can obtain it from the CFTC or an aggregator.
	•	Accessible in Startup Plan: No – LOCKED/Not provided. Must use external source (CoinGlass Startup has no CME data; CoinGlass site simply displays CFTC data separately).
	•	Community Workarounds: Yes. Use the official CFTC COT report (available as CSV or through websites). For example, the CFTC publishes BTC futures data under the “Chicago Mercantile Exchange” report. Community tools like the cot_reports Python library  or CryptoDataDownload provide this data via API .
	•	Alternative Free Source: CryptoDataDownload API – they offer free COT data for crypto . Another route: parse the weekly CFTC CSV from cftc.gov (the report code for BTC CME futures is #133741). Open source libraries (cot_reports, pycot) can fetch and parse these automatically.
	•	Python REST Example: (Using CryptoDataDownload’s API if available):
url = "https://api.cryptodatadownload.com/cftc/cme_btcf_latest"  # illustrative, not actual
data = requests.get(url).json()
# data might contain long/short totals for dealers, asset mgrs, etc.

Alternatively, use cot_reports library:

from cot_reports import COT
btc_cot = COT.get_report("BTC")
long_short = btc_cot["Leveraged Funds"]  # example category

This yields long vs short position data.

	•	Normalizer Structure: Extract the relevant figure, e.g., the net long-short difference or ratio among key categories (like “Asset Manager Long-Short Ratio” or “Leveraged Funds net position”). For simplicity, one metric could be “Leveraged Funds Net Position = X contracts”. E.g.:

return {"leveraged_funds_net": net_positions, "asset_mgr_net": net_positions2}

The panel might then say “CME Commitment: Leveraged funds net long +500 contracts”.

	•	Adapter Module Suggestion: A dedicated adapter cot_cftc.py to handle pulling and parsing CFTC data.

	•	CME Open Interest
	•	CoinGlass API Endpoint: None. This refers to total open interest on CME Bitcoin futures (regulated futures). CoinGlass futures API covers crypto exchange OI, not CME. We must fetch from CME/CFTC data.
	•	API Parameters: N/A (no CoinGlass). The total CME OI is reported in the same COT report or on CME’s site. The COT report provides total open interest and breakdown .
	•	Accessible in Startup Plan: No – not available (CoinGlass doesn’t integrate CME in API).
	•	Community Workarounds: The CFTC CoT data includes total open interest on CME BTC futures every week . Also, CME’s own website provides daily open interest numbers via their data (or historical data from Quandl). Many use the CoT data, which lists “Open Interest: X contracts” for that week.
	•	Alternative Free Source: CFTC CoT (same as above) or CME Group’s daily bulletins. Also, CryptoDataDownload likely has the total OI in their CoT API. For example, CryptoDataDownload’s tracker shows Open Interest in the table . Using their API (or CSV) might yield total OI.
	•	Python REST Example: (Continuing from previous CoT retrieval)

total_oi = btc_cot["Open Interest"]  # total open interest from COT data

If using CryptoDataDownload API, parse the JSON for the field “Open Interest”.

	•	Normalizer Structure: Provide the OI value (in number of contracts, and maybe USD equivalent). E.g.:
return {"cme_open_interest_contracts": total_oi}

The panel might display “CME Futures OI: 12,345 contracts”.

	•	Adapter Module Suggestion: cot_cftc.py (same as above) can supply this as part of the data.

	•	MicroStrategy Avg BTC Cost
	•	CoinGlass API Endpoint: None. This is a fundamental metric (not on-chain or market) – the average price paid by MicroStrategy for its BTC holdings. It must be obtained from public filings or news. There’s no direct API for this, as it updates only when MicroStrategy buys more BTC.
	•	Accessible in Startup Plan: N/A – CoinGlass does not cover individual company treasury stats via API.
	•	Community Workarounds: The value is often mentioned in financial reports or crypto news whenever MicroStrategy purchases. As of mid-2025, for example, MicroStrategy’s CEO might tweet the updated average. Community sources like BitcoinTreasuries.net track total holdings and average cost for public companies. MicroStrategy’s SEC filings (10-K/Q) list total BTC held and total acquisition cost, from which average cost = total cost / number of BTC. Reddit and Twitter usually have the latest figure after each buy announcement.
	•	Alternative Free Source: BitcoinTreasuries (web) or CoinGecko’s companies API (CoinGecko has an endpoint listing companies’ BTC holdings, though it might not include avg cost). Alternatively, one can manually compute if you know: MicroStrategy holds X BTC at total cost $Y, so average = Y/X. As of a certain date, for example, “MSTR average cost is ~$30,700 per BTC” (just an example).
	•	Python REST Example: No direct API. One could use web scraping or a static JSON source if available. For instance, if BitcoinTreasuries provided a JSON, we could parse it. Lacking that, this might be entered/updated manually in the system’s config.
	•	Normalizer Structure: Simply store the value (since it changes only when announced). E.g.:

return {"microstrategy_avg_cost_usd": 30700}

The panel can print “MicroStrategy Avg Cost: $30.7k”. This might be hardcoded or updated via script whenever new data is out.

	•	Adapter Module Suggestion: Could use a small static module or config (no external adapter needed since data is infrequently updated). If automating, an sec_scraper.py could parse MicroStrategy press releases, but that’s beyond scope. Likely treat this as a manual constant updated periodically.

	•	ETFs Premium/Discount
	•	CoinGlass API Endpoint: Yes – GET /api/bitcoin/etf/premium-discount-history . This provides the premium or discount to Net Asset Value for Bitcoin ETFs. Likely an aggregate or one needs to specify a particular fund. If aggregated, it might refer to an average premium of all spot ETFs or highlight a major one. Possibly it defaults to GBTC (though GBTC is covered in Grayscale endpoints separately). More likely, this gives a combined premium for spot ETFs vs BTC price (which generally should be near 0% for true ETFs, except minor tracking error). It might also include closed-end funds if any.
	•	API Parameters: Possibly none if aggregated, or perhaps an ETF identifier if needed (e.g., region or ticker). The presence of Premium/Discount History suggests a time series of an average premium. We might use the latest value.
	•	Accessible in Startup Plan: Likely Yes (✅ OK). Given ETF data seems included, premium history should be accessible. It’s not a highly guarded metric since it should hover around zero for open ETFs.
	•	Community Workarounds: If we interpret this as “average ETF premium”, one could compute: take a prominent ETF (like Purpose BTC ETF in Canada) and see its market price vs NAV (often published by provider). However, since spot ETFs trade at NAV (creation/redemption keeps them in line), the “premium” for true ETFs is usually minimal. Possibly they intended this to include things like closed-end funds.
	•	Alternative Free Source: If referring to closed-end fund premium (like GBTC prior to conversion), that data is public (GBTC’s market price vs its BTC per share value). For actual ETFs, premium is often near zero. Possibly the metric is more meaningful if spot ETF not yet in the US (but by 2026 perhaps US spot ETFs exist). We could use Yahoo Finance for an ETF’s market price and compare to NAV if NAV known. But since CoinGlass has it, that’s easiest.
	•	Python REST Example:


url = "https://open-api-v4.coinglass.com/api/bitcoin/etf/premium-discount-history"
params = {"interval": "1w", "limit": 1}
data = requests.get(url, headers=headers, params=params).json()
latest_pct = data['data'][-1]['premium']  # e.g. 0.5 for +0.5%

This might yield a small percentage value.

	•	Normalizer Structure: Output the percentage premium or discount. E.g.:
return {"avg_etf_premium_pct": latest_pct}

If positive, ETFs trade above NAV (premium); if negative, at a discount.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Grayscale Holdings
	•	CoinGlass API Endpoint: Yes – GET /api/grayscale/holdings-list . This should list Grayscale trust holdings, including GBTC’s BTC holdings. We specifically want the BTC amount held by Grayscale Bitcoin Trust. The endpoint likely returns all Grayscale products; filter for Bitcoin.
	•	API Parameters: None required to get the list. The list will include trust name and holdings. For GBTC, it might give number of BTC held.
	•	Accessible in Startup Plan: Yes (✅ OK). Grayscale data is included (they highlight it in API docs).
	•	Community Workarounds: Grayscale itself publishes GBTC holdings updates (daily on their site). Also, sites like bybt (now Coinglass) used to display GBTC holdings. If API wasn’t used, one could scrape Grayscale’s transparency page for GBTC.
	•	Alternative Free Source: Grayscale’s website provides daily files (JSON/CSV) of holdings per share and total AUM. For example, they often update “GBTC per share BTC” and total shares. The number of BTC = per share * shares. This could be scraped. Alternatively, use YCharts or similar if they have an API (likely not free).
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/grayscale/holdings-list"
data = requests.get(url, headers=headers).json()
gbtc = next(prod for prod in data['data'] if prod['symbol']=="GBTC")
btc_held = gbtc['BTC_holdings']

(Assuming the response has a field for BTC held). If not directly, it might give AUM and we’d convert using price. But likely it provides number of BTC.

	•	Normalizer Structure: Return the BTC holding count (and maybe USD equivalent). E.g.:
return {"gbtc_btc_holding": btc_held}

Panel might show “Grayscale BTC Holdings: 680k BTC”.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Grayscale Premium
	•	CoinGlass API Endpoint: Yes – GET /api/grayscale/premium-history . This gives the historical premium/discount of GBTC (Grayscale Bitcoin Trust) relative to its NAV. We can get the latest value (premium %).
	•	API Parameters: Possibly none except maybe an identifier if needed, but since it’s under Grayscale category, likely it defaults to GBTC.
	•	Accessible in Startup Plan: Yes (✅ OK). Grayscale premium is a well-known metric and should be included.
	•	Community Workarounds: Before CoinGlass API, people got this by comparing GBTC’s market price (from Yahoo Finance) vs the underlying BTC per share. GBTC’s BTC per share is published (currently ~0.0009 BTC/share and decreasing over time due to fees). Community trackers (like bybt) provided this for free. If needed, one could compute:
	•	Fetch GBTC stock price (Yahoo) and get NAV = (BTC price * BTC per share). Then premium = (market - NAV)/NAV.
	•	Alternative Free Source: Yahoo Finance for GBTC price + known holdings per share (available on Grayscale site or even in CoinGlass’s holdings data). The holdings-list might include “BTC per share” for GBTC, making it easy to compute premium if needed. Also, CryptoQuant user guide lists Grayscale premium under “Fund Data” (similar to Korea premium) but that requires login.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/grayscale/premium-history"
params = {"interval": "1w", "limit": 1}
premium = requests.get(url, headers=headers, params=params).json()['data'][-1]['premiumPct']

Assuming it returns a structure with premium percentage.

	•	Normalizer Structure: Output the premium/discount %. E.g.:
return {"gbtc_premium_pct": premium}

If negative, it’s a discount (e.g. “-15% discount”). The panel can format accordingly.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Bitcoin Exchange Balance
	•	CoinGlass API Endpoint: Yes – GET /api/exchange/balance/list . This gives the total BTC balance held on major exchanges, likely a list per exchange and possibly a total. We may aggregate to get the total BTC on exchanges. Also, exchange/balance/chart can give historical trend , but the current snapshot is enough for weekly.
	•	API Parameters: Possibly symbol=BTC (if needed to specify asset). The list likely defaults to BTC. It might return an array of exchanges with their BTC reserves. Summing those yields total exchange balance.
	•	Accessible in Startup Plan: Yes (✅ OK). On-chain metrics like exchange reserves are included in CoinGlass API .
	•	Community Workarounds: This data is also available from Glassnode (they have a metric “Exchange Balance – Total” on free tier with 1-day lag). CryptoQuant free charts also show exchange reserves. Without an API, some use Glassnode’s free CSV downloads or other blockchain explorers.
	•	Alternative Free Source: Glassnode Free – via their API you can get exchange_balances metric (though might need an API key and is limited). Also, CryptoQuant (no free API, but charts). For a purely free solution: some individual exchanges publish cold wallet balances, but summing manually is not feasible dynamically.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/exchange/balance/list"
data = requests.get(url, headers=headers).json()
total_btc = sum(ex['balance'] for ex in data['data'])

Now total_btc is the aggregate BTC across exchanges.

	•	Normalizer Structure: Provide the total (and possibly change from last week if comparing). E.g.:

return {"total_exchange_balance_btc": total_btc}

Panel might say “Exchange BTC Balance: 2.3M BTC” and perhaps indicate if it’s up/down vs previous period. (If needed, use exchange/balance/chart for a weekly change).

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Wallet Inflow/Outflow
	•	CoinGlass API Endpoint: Indirect – interpret this as Exchange Net Flow (the net amount of BTC flowing into or out of exchanges). CoinGlass provides net flow via GET /api/futures/coin-netflow or similar (the docs show Coin NetFlow  in both futures and spot sections). Also, the On-chain section has Exchange On-chain Transfers and Whale Transfer which might not directly give net flow. The simplest: use an exchange netflow metric if available. If not directly, compute net flow = today’s change in exchange balance (we can derive from yesterday vs today exchange balance). However, CoinGlass likely has a direct net flow endpoint for daily flows. We suspect GET /api/index/exchange-netflow or the like, but from docs: Coin NetFlow get  is listed under Other indicators (perhaps /api/index/bitcoin-netflow). It might represent the net 24h flow of BTC to exchanges (positive = inflow).
	•	API Parameters: Possibly none beyond symbol=BTC. It likely returns a time series of daily net flows in BTC.
	•	Accessible in Startup Plan: Yes (✅ OK). On-chain net flows should be available (it’s a basic on-chain metric that CoinGlass covers). Startup includes on-chain metrics .
	•	Community Workarounds: Without CoinGlass, use Glassnode’s free API for exchange net flow (they have “exchange_net_position_change” metric, which is often free with 1-day delay). Or CryptoQuant’s free chart. Alternatively, subtract yesterday’s exchange balance from today’s (if you have those values).
	•	Alternative Free Source: Glassnode API (free) – e.g. GET /v1/metrics/transactions/transfers_volume_exchanges_net (if available; Glassnode’s documentation has similar metrics). Also, blockchain.com stats don’t directly provide net flow. So Glassnode is the go-to for free with limitations.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/bitcoin-netflow"
data = requests.get(url, headers=headers).json()
net_flow_btc = data['data'][-1]['value']  # last day's net flow in BTC

If positive, that many BTC flowed into exchanges; if negative, outflows.

	•	Normalizer Structure: Output net flow (could be in BTC and maybe USD equivalent). E.g.:
return {"24h_net_flow_btc": net_flow_btc}
Panel example: “Exchange Net Flow: -5,000 BTC (24h outflow)” if negative.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Whale Revived Supply
	•	CoinGlass API Endpoint: None specific. This metric refers to the volume of old coins (held by “whales”) that have been moved (revived) after long inactivity – sometimes called “Whale Shadows” or simply old coins moved. CoinGlass does not list a direct metric for this. We need an on-chain approach.
	•	Accessible in Startup Plan: N/A – not provided by CoinGlass. This likely requires external data or calculation.
	•	Community Workarounds: Analysts often use Glassnode metrics like “Revived Supply” for coins dormant >1y or >5y that moved that day. Another approach is the Coin Days Destroyed metric focusing on large movements of old coins. Community often references Glassnode charts or Whale Alerts for big movements from ancient addresses.
	•	Alternative Free Source: Glassnode (but free tier may not include Revived Supply directly). Glassnode has “Supply Last Active X+ years” which, by difference day-over-day, gives revived supply for that cohort. E.g., drop in 5y dormant supply indicates revival. There is also a Glassnode metric “total transfer volume from wallets aged >5y”. If Glassnode API is used, one could retrieve /metrics/supply/active_more_5y_percent (for example) for two days and see the change. Alternatively, Whale Alert Twitter provides qualitative alerts for large moves. For programmatic access, no simple free API exists.
	•	Python Example: No straightforward API. If one uses Glassnode (requires API key):

# Pseudo-code using Glassnode for 5y supply
today = requests.get(glassnode_url_for_active_5y, params={"a": "BTC"}).json() 
yesterday = ... 
revived = yesterday['value'] - today['value']

This revived (in BTC) would be the amount of 5+ year old coins that moved (if positive number, supply of old coins decreased, meaning that much was revived).

	•	Normalizer Structure: Output the estimated revived supply (e.g., “5+yr old coins moved today: X BTC”).
return {"revived_5y_coins_btc": revived}

If the panel wants a broader “whale supply moved”, we might just report this number.

	•	Adapter Module Suggestion: Possibly use an onchain_fallback.py module. This could fetch Glassnode data or any on-chain source. If not feasible, mark this metric as MISSING or to be updated manually from research reports.

	•	Miner Outflows
	•	CoinGlass API Endpoint: None. CoinGlass does not list miner-specific metrics in their API v4 docs. We need to rely on on-chain data: the amount of BTC leaving miner addresses.
	•	Accessible in Startup Plan: Not available – EXTERNAL REQUIRED.
	•	Community Workarounds: The go-to is Glassnode which has “Miner Outflow Volume”. Indeed Glassnode’s API has GET /v1/metrics/transactions/transfers_volume_from_miners_sum . This gives the total BTC transferred out of miner wallets, typically per day. CryptoQuant also offers Miner Outflow (paid).
	•	Alternative Free Source: Glassnode free – it may allow daily resolution of miner outflows with a free API key. Also, the Blockchain.info Stats API provides “miners’ revenue” but not outflows. However, since miner outflow is usually smaller than revenue (they may hold some), an approximation could be revenue as an upper bound of possible outflow. But better to use Glassnode’s actual outflow metric.
	•	Python REST Example: (using Glassnode’s free API)

import requests
GN_API = "YOUR_GLASSNODE_API_KEY"
url = "https://api.glassnode.com/v1/metrics/transactions/transfers_volume_from_miners_sum"
params = {"a": "BTC", "i": "24h", "api_key": GN_API}
data = requests.get(url, params=params).json()
miner_outflow = data[-1]['v']  # last day value in BTC

This yields the total BTC that miners sent out in the past 24h.

	•	Normalizer Structure: Provide the volume (in BTC, and maybe USD). E.g.:

return {"daily_miner_outflow_btc": miner_outflow}

Panel can say “Miner Outflows: X BTC in last 24h”.

	•	Adapter Module Suggestion: miner_metrics.py – a custom adapter to gather miner data (could use Glassnode API calls).

	•	Miner Revenue
	•	CoinGlass API Endpoint: None. This is the total revenue miners earn (block rewards + fees), typically expressed per day in USD. Not provided by CoinGlass API.
	•	Accessible in Startup Plan: N/A.
	•	Community Workarounds: The Blockchain.com Stats API is perfect here. It provides miners_revenue_usd and miners_revenue_btc for each day . This is a free and direct source. Glassnode also has Miner Revenue metrics but blockchain.info is free and easy.
	•	Alternative Free Source: Blockchain.com – e.g. calling https://api.blockchain.info/stats returns JSON including miners_revenue_usd  for the last 24h. This can be used without an API key.
	•	Python REST Example:

stats = requests.get("https://api.blockchain.info/stats").json()
revenue_usd = stats["miners_revenue_usd"]
revenue_btc = stats["miners_revenue_btc"]

This gives the latest 24h miner revenue (the example shows fields in the stats response ).

	•	Normalizer Structure: Provide revenue in USD (and optionally BTC). E.g.:

return {"daily_miner_revenue_usd": revenue_usd, "daily_miner_revenue_btc": revenue_btc}

Panel might state “Miner Revenue: $X million per day”.

	•	Adapter Module Suggestion: miner_metrics.py (same adapter could handle outflows and revenue, using different sources).

	•	LTH Supply (Long-Term Holder Supply)
	•	CoinGlass API Endpoint: Yes – GET /api/index/bitcoin-long-term-holder-supply is available (from docs listing: Bitcoin Long Term Holder Supply get ). This gives the total BTC held by long-term holders (often defined as >155 days old coins).
	•	API Parameters: None aside from it being BTC-specific. It likely returns a value or time series. We can take the latest value (perhaps as a percentage of supply or an absolute BTC amount). Possibly it returns both absolute and percent. Given the naming, probably absolute amount of BTC.
	•	Accessible in Startup Plan: Yes (✅ OK). This is an on-chain indicator included in CoinGlass’s “Other” metrics. It was explicitly noted that CoinGlass includes LTH supply.
	•	Community Workarounds: Glassnode is the original source for such metrics. Glassnode’s free tier actually often shares Total LTH Supply (with 1-day lag). If not via CoinGlass, one could use Glassnode’s API (/metrics/supply/long_term_holders etc., if available) or take it from public charts.
	•	Alternative Free Source: Glassnode (with API key) – metric Supply Last Active > 155 Days approximates LTH supply. Some community dashboards (LookIntoBitcoin) show HODL wave data but not easily scriptable. If needed, Glassnode is best.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/bitcoin-long-term-holder-supply"
data = requests.get(url, headers=headers).json()
lth_supply = data['data'][-1]['value']  # possibly in BTC

This yields the latest LTH supply (e.g. 14 million BTC).

	•	Normalizer Structure: Provide either the BTC amount or percentage of circulating supply. If just BTC:
return {"lth_supply_btc": lth_supply}
Panel could show it as “LTH Supply: X BTC (Y% of circulating)”. We can compute Y% by dividing by 21e6 or current supply (~19.3M). If CoinGlass gives percent, use that directly.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	STH Supply (Short-Term Holder Supply)
	•	CoinGlass API Endpoint: Yes – GET /api/index/bitcoin-short-term-holder-supply (from docs: Bitcoin Short Term Holder Supply get ). This is complementary to LTH supply. It might also be given directly, or one can do total supply minus LTH supply. CoinGlass provides it, so use directly.
	•	API Parameters: None needed (BTC specific).
	•	Accessible in Startup Plan: Yes (✅ OK). Provided alongside LTH metrics.
	•	Community Workarounds: Similarly via Glassnode (short-term = total circulating minus long-term). If not via API, one could subtract LTH from circulating supply. Circulating supply is easily available (e.g. blockchain.info totalbc field ).
	•	Alternative Free Source: Glassnode or manual calculation.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/bitcoin-short-term-holder-supply"
sth_supply = requests.get(url, headers=headers).json()['data'][-1]['value']

(Alternatively, compute: sth_supply = circulating_supply - lth_supply).

	•	Normalizer Structure:
return {"sth_supply_btc": sth_supply}

Possibly also percent of supply.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	LTH SOPR (Long-Term Holder Spent Output Profit Ratio)
	•	CoinGlass API Endpoint: Yes – GET /api/index/bitcoin-long-term-holder-sopr . SOPR indicates profit ratio of spent outputs; LTH SOPR specifically looks at coins spent by long-term holders.
	•	API Parameters: None beyond asset. Returns the SOPR value (typically a float around 1; >1 means LTH are selling at profit on average).
	•	Accessible in Startup Plan: Yes (✅ OK). LTH SOPR is listed as available .
	•	Community Workarounds: Glassnode is known for SOPR metrics. LTH-SOPR might be an advanced metric on Glassnode (which likely requires at least a mid-tier). If not via CoinGlass, a workaround is not trivial since one must segregate outputs by holding time. Better to rely on CoinGlass.
	•	Alternative Free Source: None readily free. Standard SOPR (all market) is sometimes shared freely, but LTH vs STH breakdown is unique to advanced on-chain analysis. We assume no free equivalent.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/index/bitcoin-long-term-holder-sopr"
lth_sopr = requests.get(url, headers=headers).json()['data'][-1]['value']

This gives the latest LTH SOPR (e.g. 1.05).

	•	Normalizer Structure:

return {"lth_sopr": round(lth_sopr, 3)}

Panel: “LTH SOPR: 1.05 (LTH are in profit)”.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	STH SOPR (Short-Term Holder SOPR)
	•	CoinGlass API Endpoint: Yes – GET /api/index/bitcoin-short-term-holder-sopr . Provides SOPR for short-term holders (usually more volatile).
	•	API Parameters: None (BTC only).
	•	Accessible in Startup Plan: Yes (✅ OK). Included with LTH SOPR.
	•	Community Workarounds: Similar to LTH SOPR, not freely available except via advanced data providers.
	•	Alternative Free Source: None easily.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/bitcoin-short-term-holder-sopr"
sth_sopr = requests.get(url, headers=headers).json()['data'][-1]['value']

•	Normalizer Structure:
return {"sth_sopr": round(sth_sopr, 3)}

Panel can compare it to 1, etc.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	LTH-MVRV (Long-Term Holder MVRV)
	•	CoinGlass API Endpoint: No direct metric for LTH-MVRV, but we can compute it. MVRV = Market Value / Realized Value. For LTH subset, LTH-MVRV = (Current Price) / (LTH’s average cost basis). We have the pieces: CoinGlass provides LTH Realized Price  (the average price at which LTH acquired their coins). So: LTH-MVRV = current BTC price / LTH realized price.
	•	API Parameters: To get LTH realized price, use GET /api/index/bitcoin-long-term-holder-realized-price (from docs: Realized Price for LTH is listed ). Also get current price (e.g. from spot data).
	•	Accessible in Startup Plan: Realized prices are provided (likely accessible, part of those indicators). Yes for the needed endpoints.
	•	Community Workarounds: Without CoinGlass, one could use Glassnode’s data: Glassnode gives LTH realized price (perhaps not free). Or manually compute if one has LTH realized cap and LTH supply. (LTH Realized Price = LTH Realized Cap / LTH Supply). Glassnode’s free tier might not give all of that. So better to rely on CoinGlass or skip if not available.
	•	Alternative Free Source: Possibly compute from values we have: If we know LTH supply (from CoinGlass) and we know total realized cap and total market cap (free from some sources), we could approximate LTH realized cap as LTH supply * LTH realized price (if we had LTH realized price from an external or assumed). This is complex to do externally; best via CoinGlass.
	•	Python REST Example:
# Get LTH realized price
url = "https://open-api-v4.coinglass.com/api/index/bitcoin-long-term-holder-realized-price"
lth_realized_price = requests.get(url, headers=headers).json()['data'][-1]['value']
# Get current price from spot markets
spot = requests.get("https://open-api-v4.coinglass.com/api/spot/coins-markets", headers=headers).json()
btc_price = next(item for item in spot['data'] if item['symbol']=="BTC")['price']
lth_mvrv = btc_price / lth_realized_price

•	Normalizer Structure:
return {"lth_mvrv": round(lth_mvrv, 2)}

If >1, LTH cohort is in profit on average; if <1, at a loss. Panel can note that.

	•	Adapter Module Suggestion: This calculation can be done in the normalizer. No new adapter – data from coinglass_v4.py (spot price and LTH realized price) is used.

	•	STH-MVRV (Short-Term Holder MVRV)
	•	CoinGlass API Endpoint: No direct metric similarly. Compute as current price / STH realized price. CoinGlass provides STH Realized Price . Use that.
	•	API Parameters: Endpoint likely GET /api/index/bitcoin-short-term-holder-realized-price.
	•	Accessible in Startup Plan: Yes (the realized price endpoints for LTH/STH are present and should be accessible).
	•	Community Workarounds: Glassnode (if available) or calculation from STH realized cap and supply if one has them. Not trivial externally.
	•	Alternative Free Source: Unavailable, so rely on CoinGlass or omit.
	•	Python REST Example: Similar to LTH:

sth_realized_price = requests.get("https://open-api-v4.coinglass.com/api/index/bitcoin-short-term-holder-realized-price", headers=headers).json()['data'][-1]['value']
sth_mvrv = btc_price / sth_realized_price

•	Normalizer Structure:
return {"sth_mvrv": round(sth_mvrv, 2)}

STH-MVRV >1 indicates short-term holders in profit on average.

	•	Adapter Module Suggestion: Calculated via coinglass_v4.py data.

	•	RHODL Ratio
	•	CoinGlass API Endpoint: Yes – GET /api/index/bitcoin-rhodl-ratio . The RHODL Ratio is a market-cycle indicator comparing short-term vs long-term realized value (originally from Philip Swift). CoinGlass lists it directly.
	•	API Parameters: None beyond asset. It returns the current RHODL ratio (and perhaps a time series).
	•	Accessible in Startup Plan: Yes (✅ OK). It’s in the Other indicators list (and was noted as included ).
	•	Community Workarounds: The formula uses Realized Cap HODL waves (specifically 1-week vs 1-2 year coin age bands). Hard to compute manually. Usually one gets it from LookIntoBitcoin or Glassnode (Glassnode provides RHODL in their advanced metrics). Without API, one could find occasional updates on blogs. But now CoinGlass provides it.
	•	Alternative Free Source: Not really free API. One could approximate if they had detailed HODL wave data (which Glassnode free might not give at needed resolution). So use CoinGlass.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/index/bitcoin-rhodl-ratio"
rhodl = requests.get(url, headers=headers).json()['data'][-1]['value']

Yields the current RHODL ratio (a number that in past cycles peaked above 50,000 etc., it’s a specific index value).

	•	Normalizer Structure:
return {"rhodl_ratio": round(rhodl, 2)}

Panel likely will just show it or mention if it’s in high/low regime.

	•	Adapter Module Suggestion: coinglass_v4.py.

Cycle & Değerleme (Macro Cycle Indicators – Monthly)
	•	MVRV Ratio
	•	CoinGlass API Endpoint: Not explicitly listed. Surprisingly, CoinGlass docs did not show a direct “MVRV Ratio” endpoint (they have many other indicators, but MVRV was not in the list we saw). It might be absent or under a different name. If it’s not provided, we must compute or get externally. MVRV = Market Cap / Realized Cap. We can get Market Cap (price * circulating supply) and Realized Cap (sum of coin values when last moved). CoinGlass does provide realized price or other metrics, but not realized cap outright. However, realized price * circulating supply ≈ realized cap. Alternatively, they might include MVRV indirectly via other “Peak Indicators” or as part of NUPL/Reserve Risk sets. Given uncertainty, assume no direct endpoint (thus fallback needed).
	•	Accessible in Startup Plan: No direct metric – LOCKED/EXTERNAL.
	•	Community Workarounds: CryptoQuant and Glassnode both provide MVRV charts. CryptoQuant’s “Bitcoin: MVRV Ratio” is accessible on their site  (likely behind login for API). Glassnode’s API has MVRV (but maybe not on free tier). Another approach: use free data – Market Cap (from price * supply) and Realized Cap (available from e.g. Coin Metrics community data or Glassnode’s free weekly numbers). Actually, realized cap can be obtained from Blockchain.com’s stats? (Not directly, but maybe not). Possibly use an approximation: Glassnode sometimes shares realized price which can yield realized cap when multiplied by current supply. Interestingly, CoinGlass does list “Profitable Days” and “NUPL” etc., but not MVRV. We may have to calculate.
	•	Alternative Free Source: CoinMarketCap API for market cap (or just price * supply), and Coin Metrics Community Data for realized cap. Coin Metrics offers some free community metrics CSVs; realized cap might be one. If not, Glassnode’s free tier might allow realized price (which is average purchase price of all coins). Realized price * circulating supply = Realized Cap. For example, if realized price is $X, multiply by ~19.3M to get realized cap. Actually, realized price in July 2025 was around $19k, times supply ~19M gives realized cap ~ $361B, and market cap maybe $550B, MVRV ~1.52. We could also use the Blockchain.info stats for “total_btc_sent” etc. – not directly helpful for realized cap. So likely a manual formula route.
	•	Python Calculation Example:

# Using external data for demonstration:
market_cap = current_price * circulating_supply  # e.g. price from Coinglass spot, supply from blockchain.info stats "totalbc" which is satoshis *1e-8
circ = requests.get("https://api.blockchain.info/stats").json()['totalbc'] / 1e8
price = btc_price  # from earlier spot fetch
market_cap = price * circ
# assume realized price from CoinGlass's Reserve Risk or NUPL context if available, otherwise set manually or from Glassnode:
realized_price = 19000  # placeholder, ideally from an API
realized_cap = realized_price * circ
mvrv = market_cap / realized_cap

Without a direct feed, this is rough. If Glassnode API is available: GET /v1/metrics/market/mvrv could exist (not sure publicly). CryptoQuant requires login.

	•	Normalizer Structure
return {"mvrv_ratio": round(mvrv, 2)}

If this metric cannot be fetched or computed reliably in code, mark as missing or to be manually updated. Possibly treat it as part of “Bull Market Peak Indicators” if CoinGlass provides those (they might have a combined endpoint that includes MVRV Z, etc.).

	•	Adapter Module Suggestion: Perhaps use onchain_fallback.py to compute this (fetch price, supply, use a constant or external for realized price/cap). If too uncertain, skip automated retrieval.

	•	MVRV Z-Score
	•	CoinGlass API Endpoint: Not directly listed. It might be included under “Bull Market Peak Indicators” . That entry could encapsulate MVRV Z-Score since it’s a known peak indicator. If so, perhaps GET /api/index/bull-market-peak returns MVRV Z among others. But without confirmation, assume we need external.
	•	Accessible in Startup Plan: Likely No direct metric (if it’s hidden under bull indicators, maybe only on higher plan or not at all).
	•	Community Workarounds: MVRV Z-Score is well known and often charted freely. LookIntoBitcoin provides a chart and the current value, but no API. CryptoQuant also has it (again behind login) . Could approximate by formula: Z-score = (Market Cap – Realized Cap) / stdev(Market Cap – Realized Cap) over history. That’s complicated to compute on the fly without historical data readily. Better to retrieve from a source if possible.
	•	Alternative Free Source: Possibly Glassnode Studio shows MVRV Z but no API without paying. A creative approach: some open-source implementations exist where people have computed it offline. But for our integration, likely we mark it external.
	•	Python Example: Not readily available. If one had historical data, compute Z. Without that, might have to skip or rely on manual entry from a known current value (e.g. if someone publishes “MVRV Z = 2.5”). This is not ideal for automation.
	•	Normalizer Structure: If we had it:
return {"mvrv_z_score": value}

Possibly update this monthly from research.

	•	Adapter Module Suggestion: No direct adapter; include in onchain_fallback.py if any source is found (perhaps parse from a known CSV or source updated periodically).

	•	Mayer Multiple
	•	CoinGlass API Endpoint: None. Mayer Multiple = Price / 200-day moving average of Price. CoinGlass lists general MA, but not specifically the Mayer Multiple as an index. We can calculate it since we have price data.
	•	Accessible in Startup Plan: N/A (calculation needed).
	•	Community Workarounds: Very straightforward: need the 200-day moving average. This can be computed from historical price. If we can fetch daily price history from CoinGlass or another API, we can compute the 200-day average and then the multiple. Many community sites track the Mayer Multiple (and threshold 2.4 etc.). We can use free price data (Yahoo or CoinGlass OHLC).
	•	Alternative Free Source: CoinGlass could provide the 200-day MA via their indicators (they list MA, EMA endpoints ). Actually, yes: GET /api/indicator/futures/moving-average might allow retrieving MA for given length. If that endpoint exists, we could directly get the 200-day MA from CoinGlass. If so, that’s simpler: call MA endpoint with period=200 days. Otherwise, use daily price series.
	•	Python REST Example (Method 1 - CoinGlass MA):
url = "https://open-api-v4.coinglass.com/api/indicator/futures/moving-average"
params = {"symbol": "BTC", "window": 200, "interval": "1d"}
ma200 = requests.get(url, headers=headers, params=params).json()['data'][-1]['value']
price = btc_price  # from spot data
mayer = price / ma200

(If direct MA endpoint not accessible, Method 2: fetch 200 days of price via /api/spot/price/history and compute average in Python.)

	•	Normalizer Structure:
return {"mayer_multiple": round(mayer, 2)}

Panel note: historically >2.4 is a cycle top indicator, etc.

	•	Adapter Module Suggestion: If using CoinGlass MA, then coinglass_v4.py. If computing manually from prices (maybe using a local Python rolling average), still under the same adapter or a small function in normalizer.

	•	Puell Multiple
	•	CoinGlass API Endpoint: Yes – GET /api/index/puell-multiple . This is explicitly available. The Puell Multiple = (Daily miner revenue in USD) / (365-day avg of daily miner revenue). CoinGlass likely calculates and provides it directly.
	•	API Parameters: None needed (just BTC). It returns the value (a number that historically peaks above ~8 or so in bull tops).
	•	Accessible in Startup Plan: Yes (✅ OK). It was enumerated in their indicators list .
	•	Community Workarounds: It’s well-known; could be computed using blockchain.com data (since we have daily miner revenue from blockchain.info and can average 365 days – but that requires a year of data, doable by calling charts API). But since CoinGlass has it, no need.
	•	Alternative Free Source: Blockchain.com Charts API – one could retrieve a year of miners_revenue_usd and compute average, then divide today’s revenue by avg. It’s quite feasible if needed. Or see if CryptoQuant posts it. But CoinGlass covers it nicely.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/index/puell-multiple"
puell = requests.get(url, headers=headers).json()['data'][-1]['value']

This gives current Puell Multiple.

	•	Normalizer Structure:
return {"puell_multiple": round(puell, 2)}

Panel usage: e.g. “Puell: 1.3 (low) or 8 (high) etc.”

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	NVT Ratio
	•	CoinGlass API Endpoint: Not clearly listed. NVT = Network Value to Transactions ratio (Market Cap / On-chain Transaction Volume, typically daily). CoinGlass did not show “NVT” in the extracted docs. Possibly missing. We’ll use fallback.
	•	Accessible in Startup Plan: No direct (assuming not present).
	•	Community Workarounds: The ingredients: market cap and daily transaction volume. We have price and supply for market cap, and on-chain volume (blockchain.info provides “estimated_transaction_volume_usd” in stats  which is daily on-chain volume). Yes, Blockchain.info stats includes estimated_transaction_volume_usd (which is the total value of BTC transacted on-chain in last 24h, excluding popular addresses) . We can use that for volume. Then NVT = market_cap / daily_tx_volume. This is straightforward and free.
	•	Alternative Free Source: As above, Blockchain.com or Glassnode (Glassnode’s NVT might use a smoother, but we can do raw).
	•	Python REST Example:

stats = requests.get("https://api.blockchain.info/stats").json()
mcap = btc_price * stats["n_btc_mined"] / 1e8  # approximate market cap using total BTC mined (n_btc_mined is actually new mined? Might use totalbc instead)
# Better: use totalbc (total circulating satoshis) from stats:
circ = stats["totalbc"] / 1e8  # current circulating supply
mcap = btc_price * circ
volume = stats["estimated_transaction_volume_usd"]
nvt = mcap / volume

Note: totalbc is total mined in satoshis ; estimated_transaction_volume_usd is daily USD volume. Use those.

	•	Normalizer Structure:
return {"nvt_ratio": round(nvt, 2)}

Panel context: high NVT can mean overvaluation or low network usage relative to price.

	•	Adapter Module Suggestion: onchain_fallback.py (since we use blockchain.info).

	•	Bitcoin Bubble Index
	•	CoinGlass API Endpoint: Yes – GET /api/index/bitcoin-bubble-index . This is a proprietary indicator by CoinGlass (AFAIK originally from 2014 by Willy Woo). CoinGlass lists it, so use it directly.
	•	API Parameters: None beyond asset. Returns an index value. The Bubble Index attempts to identify speculative bubble phases.
	•	Accessible in Startup Plan: Yes (✅ OK). It’s in the indicator list  and should be accessible.
	•	Community Workarounds: Not widely available elsewhere, as it’s somewhat specific. Without CoinGlass, most would ignore this metric or use alternatives like NUPL or Mayer multiple. CoinGlass providing it is easiest.
	•	Alternative Free Source: None known.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/index/bitcoin-bubble-index"
bubble = requests.get(url, headers=headers).json()['data'][-1]['value']
•	Normalizer Structure:
return {"bubble_index": round(bubble, 2)}
Interpretation likely requires context (CoinGlass might describe thresholds). The panel might just output the number or a category (e.g. “Bubble Index: 3 (moderate)”).

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Ahr999 Index
	•	CoinGlass API Endpoint: Yes – GET /api/index/ahr999 . This index (AHR999) is an indicator comparing price to 2-year moving average (similar to Mayer multiple concept but specific thresholds). CoinGlass supports it.
	•	API Parameters: None besides asset.
	•	Accessible in Startup Plan: Yes (✅ OK). Listed among other indicators .
	•	Community Workarounds: This is a specific index popularized on Chinese forums. Outside CoinGlass, it’s not common; one could calculate if definition known (I believe AHR999 = price / 2-year MA * some constant). But since CoinGlass has it, no need.
	•	Alternative Free Source: Not really available except on CoinGlass’s own site where they display it.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/ahr999"
ahr = requests.get(url, headers=headers).json()['data'][-1]['value']

•	Normalizer Structure:
return {"ahr999": round(ahr, 2)}

(Often, AHR999 < 1.2 indicates undervalued, etc., but we just provide the number).

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	2-Year MA Multiplier
	•	CoinGlass API Endpoint: Yes – GET /api/index/two-year-ma-multiplier . This gives the ratio of price to the 2-year moving average (and possibly the upper band which is 5x the 2-year MA). The “multiplier” usually refers to price / (2-year MA).
	•	API Parameters: None. It returns a value (e.g. if price is exactly 2-year MA, multiplier = 1).
	•	Accessible in Startup Plan: Yes (✅ OK). It’s listed .
	•	Community Workarounds: Could compute if needed: 2-year MA can be derived from price history; multiplier = price / MA. But since provided, use theirs.
	•	Alternative Free Source: Without API, one could compute using price data (730-day moving average). But easier to use CoinGlass or skip.
	•	Python REST Example:

url = "https://open-api-v4.coinglass.com/api/index/tow-year-ma-multiplier"
ma2x = requests.get(url, headers=headers).json()['data'][-1]['value']

(Assuming “tow-year” is a typo and actual endpoint uses “two-year-ma-multiplier”).

	•	Normalizer Structure:
return {"two_year_ma_multiplier": round(ma2x, 2)}

Panel context: e.g. if ~5, price is 5x the 2-year MA (historically very high).

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	4-Year MA
	•	CoinGlass API Endpoint: Not explicitly listed. Possibly not provided as a standalone. 4-Year Moving Average might not be directly given (2-year was given likely due to known model). We can calculate 4-year MA or possibly it’s part of “200-Week Moving Avg Heatmap” (200-week MA ~ 3.8 years). The docs list “200-Week Moving Avg Heatmap” . So they do have the 200-week (which is ~3.8y) MA data, perhaps as an endpoint. If so, use that. Or simply compute from price history if needed.
	•	Accessible in Startup Plan: If they have “200-week MA Heatmap” it might be included. But extracting the value from a heatmap might be unnecessary since we can compute or find 200-week MA value easily.
	•	Community Workarounds: 200-week MA is a famous metric (never been broken for long until 2022). It’s easily computed from price data. Also, it’s often published (e.g. PlanB posts it).
	•	Alternative Free Source: Yahoo Finance for historical daily prices then compute 200-week (which is 1400 days) average. Or see if blockchain.com or other API has it (not directly). We might do a quick calculation offline. But given monthly frequency, even manually updating occasionally is fine.
	•	Python Example (compute):
# Fetch ~1400 days of daily price from CoinGlass or CoinGecko
prices = requests.get("https://open-api-v4.coinglass.com/api/spot/price/history", 
                      params={"symbol":"BTC", "interval":"1d", "limit":1400}, headers=headers).json()
avg_200w = sum(pt['close'] for pt in prices['data']) / len(prices['data'])

This approximates the 200-week MA.

	•	Normalizer Structure:
return {"200w_ma_usd": round(avg_200w, 0)}
And/or as a ratio to current price if needed.

	•	Adapter Module Suggestion: Possibly handled in coinglass_v4.py or computed in normalizer.

	•	Stock-to-Flow
	•	CoinGlass API Endpoint: Yes – GET /api/index/stock-to-flow-model . CoinGlass provides the S2F model value. Likely the current projected price per the original S2F model (or ratio). Possibly returns both the S2F ratio and the model price. The context suggests it’s an index – likely they provide the model price.
	•	API Parameters: None beyond asset.
	•	Accessible in Startup Plan: Yes (✅ OK). Listed and presumably accessible.
	•	Community Workarounds: S2F model is a known formula depending on time (it steps up after halvings). One can calculate it if needed (the formula uses current supply growth rate). But easier to use provided data.
	•	Alternative Free Source: PlanB’s published charts (no API, but formula is public: S2F = A * stock^B etc.). But given CoinGlass has it, use theirs.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/stock-to-flow-model"
s2f_price = requests.get(url, headers=headers).json()['data'][-1]['value']

This likely returns the model price in USD.

	•	Normalizer Structure:

return {"s2f_model_price_usd": round(s2f_price, 0)}

Optionally compare with actual price (to see divergence).

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Pi Cycle Top
	•	CoinGlass API Endpoint: Yes – GET /api/index/pi-cycle-top-indicator . This indicator checks if short-term MA crosses long-term MA multiple (111-day vs 350-day*2) – historically signaled cycle tops. CoinGlass likely gives a boolean or an index gap. Possibly they provide the difference between those MAs or a signal (1/0). Perhaps they provide both moving average values. We might just present it as a yes/no or the indicator value.
	•	API Parameters: None.
	•	Accessible in Startup Plan: Yes (✅ OK). It’s listed and presumably included.
	•	Community Workarounds: Without API, one can compute the two MAs from price history and see if 111d MA > 2x350d MA, etc. Many community charts show it. But since provided, that’s easiest.
	•	Alternative Free Source: Manual computation from price data (feasible if needed).
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/pi-cycle-top-indicator"
pi = requests.get(url, headers=headers).json()['data'][-1]

The response might include values like {"111dMA": X, "350dMA*2": Y} or a ratio. If not, maybe a signal value. We’d interpret accordingly.

	•	Normalizer Structure: Possibly output the ratio of 111-day MA to (2 * 350-day MA). If >1, top signal triggered. E.g.:
ratio = pi['value']  # if they give a ratio or difference
return {"pi_cycle_ratio": round(ratio, 3)}

Or simply a boolean flag if provided.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Golden Ratio Multiplier
	•	CoinGlass API Endpoint: Yes – GET /api/index/golden-ratio-multiplier . This is an indicator using multiples of the 350-day MA by golden ratio powers (popularized by Philip Swift). CoinGlass provides it. Possibly they give current price vs certain band or an index number indicating position. Might require interpretation. They might output something like which band the price is in. But perhaps a simpler output: the next major multiple level etc. We may just report current vs one of the multiples. For integration, we can fetch and present the top multiplier value or an index.
	•	API Parameters: None beyond asset.
	•	Accessible in Startup Plan: Yes (✅ OK). Provided in list.
	•	Community Workarounds: Without direct API, one can compute 350d MA and then multiply by φ (1.618), φ^2, etc., and compare to price. But since it’s given, we use theirs.
	•	Alternative Free Source: None directly, aside from manual calc.
	•	Python REST Example:
url = "https://open-api-v4.coinglass.com/api/index/golden-ratio-multiplier"
grm = requests.get(url, headers=headers).json()['data'][-1]['value']

Unsure what value represents here – possibly a normalized score or maybe the upper band value. If documentation not clear, we might skip detailed integration beyond acknowledging metric.

	•	Normalizer Structure: If we interpret value as, say, price divided by 350d MA, then:
return {"gr_multiplier": round(grm, 2)}

If >φ^3 (~4.24) historically top, etc. The panel might require more context. Possibly leave it as index number.

	•	Adapter Module Suggestion: coinglass_v4.py.

	•	Hash Ribbons
	•	CoinGlass API Endpoint: None given. Hash Ribbons (indicator of miner capitulation and recovery) isn’t listed. It requires 30d and 60d hash rate moving averages. Not provided by CoinGlass v4 as per docs.
	•	Accessible in Startup Plan: No – EXTERNAL REQUIRED.
	•	Community Workarounds: Compute from network hash rate data. The Hash Ribbons give a buy signal when the short-term hash MA crosses above long-term after a period of distress. We can get hash rate from blockchain.info (they have a chart for total hash rate TH/s) but we need to compute 30d and 60d moving averages, then detect cross. Could be done with historical data. Another approach: some websites (LookIntoBitcoin) publish if the signal is active. Without building time-series logic, one may simplify by indicating whether miners are in capitulation. Possibly, one might check the trend of hash rate or if 30d < 60d (capitulation ongoing) or 30d > 60d (recovery).
	•	Alternative Free Source: Blockchain.com charts API can give historical hash rate. We could fetch 2 months of daily hash rate via charts/hash-rate and compute. Alternatively, Glassnode’s free API might allow hash rate metrics. But direct quick integration is complex. If not automating fully, we could mark when last buy signal occurred (manually update). But for completeness, we try automation:
	•	Python Example (conceptual):
# Fetch 90 days of hash rate data from blockchain.com
hr_data = requests.get("https://api.blockchain.info/charts/hash-rate?timespan=90days&format=json").json()['values']
# values list of {"x": timestamp, "y": TH/s}
# Compute 30d and 60d averages of y:
import pandas as pd
df = pd.DataFrame(hr_data)
df['MA30'] = df['y'].rolling(window=30).mean()
df['MA60'] = df['y'].rolling(window=60).mean()
latest = df.iloc[-1]
signal = (latest['MA30'] > latest['MA60']) and (df['MA30'].iloc[-15] < df['MA60'].iloc[-15])

Here signal True could indicate a recent cross (buy signal). This is a rough approach.

	•	Normalizer Structure: Could output a boolean or status:
return {"hash_ribbons_signal": "BUY" if signal else "–"}

or output the current ratio of MA30/MA60 to indicate phase.

	•	Adapter Module Suggestion: onchain_fallback.py (since using blockchain info or similar). This might be complex; if not reliable, mark this metric as to be manually monitored.

	•	Bitcoin Power Law
	•	CoinGlass API Endpoint: None. The “Power-Law Corridor” is a model (not a single metric) – it gives an upper and lower bound on price on a log-log scale time trend. There’s no simple number to fetch; it’s typically a chart/band. We can’t easily integrate this via API.
	•	Accessible in Startup Plan: N/A.
	•	Community Workarounds: The Power Law bands are published on places like Glassnode insights or blogs. No API. One could theoretically compute regression on past price data to get the trend line, but beyond scope.
	•	Alternative Free Source: None for automation. Likely to be handled qualitatively or skipped in an automated panel.
	•	Approach: Mark as MISSING or provide last known upper/lower band if manually entered. Possibly skip printing if not fetched.
	•	Adapter Module Suggestion: None (would require a custom script offline).
	•	Delta Top Model
	•	CoinGlass API Endpoint: None. The Delta Cap model yields a theoretical top price (Realized Cap * 2 – Average Cap). That’s a specific calculation. We could attempt if we had Realized Cap and Average Market Cap. Realized Cap we might approximate (see MVRV), Average Market Cap over entire history is harder to get without historical data. So likely not automatable easily.
	•	Accessible in Startup Plan: N/A.
	•	Community Workarounds: People reference charts (e.g. via LookIntoBitcoin) but no programmatic source.
	•	Alternative Free Source: None easily.
	•	Approach: Probably mark as MISSING or manually input the current Delta Top value if known from an analysis. This is not frequently cited in daily context, so possibly can be omitted or commented in panel output as not available.
	•	Adapter Module Suggestion: None (manual).

Conclusion: The research above provides a comprehensive catalog of each metric needed for “Savaş Paneli”, including primary CoinGlass API endpoints (with full URLs and parameters) and whether they are accessible under the Startup plan or require external data. For those requiring external sources, we’ve identified community or free alternatives (Reddit discussions, GitHub libraries, public APIs)  . We also included Python REST call examples for each case, demonstrating how to fetch the data (either from CoinGlass or fallback APIs) and suggested how to normalize the raw outputs into the panel’s JSON/text format.

This catalog is organized by the panel’s metric groups (Derivatives/Liquidity, Spot/Institutional, Momentum, Smart Money, Cycle/Valuation) and can be used as an integration guide. Developers can implement the adapters as suggested (e.g. coinglass_v4.py for CoinGlass metrics, and specialized modules like cot_cftc.py for CME data, miner_metrics.py for miner stats, onchain_fallback.py for certain on-chain metrics) to fetch and normalize these metrics. The final panel CLI (btc command) will iterate through this registry, attempt CoinGlass API calls for each metric (status “OK”), or fall back to the community sources (for metrics marked EXTERNAL_REQUIRED or LOCKED), and then output both a JSON object and a formatted text summary of the full Savaş Paneli.




——————————————————————————————————————————————————————————————————————————————————————————————————

2. Araştırma;

Automating the “Savaş Paneli” BTC Data Dashboard

CoinGlass API Endpoint Coverage and Access Levels

CoinGlass API Endpoints: CoinGlass’s V4 API provides over 100 endpoints covering Futures, Spot, Options, ETF, On-Chain, and Indicator data  . Under the Startup plan (~80+ endpoints), most core endpoints are accessible, while some advanced metrics are locked behind higher plans (Standard/Professional)  . A few desired metrics aren’t available on CoinGlass at all, but can be obtained from external free sources like CryptoQuant, Glassnode, Santiment, or IntoTheBlock.
	•	Accessible with Startup Plan: Standard market data and popular indicators. For example, derivatives data (open interest, funding rates, liquidations), spot market data (prices, volumes), basic on-chain metrics (exchange reserves, BTC net flows), and widely-cited indices (e.g. Fear & Greed Index, stock-to-flow, etc.) are included in Startup  . The Startup plan offers 1-min data updates and ~80 endpoints, sufficient for most dashboard needs . (E.g. the global BTC futures open interest history and funding rates are available to Startup users .)
	•	Locked (Upgrade Required): Some specialized or institution-grade endpoints require a Standard or higher plan. These likely include certain on-chain analytics and long-term holder metrics that CoinGlass integrates (often originally from Glassnode). Examples: Long/Short Holder SOPR, LTH Realized Price, RHODL Ratio, Reserve Risk and similar advanced on-chain indicators are probably not in the base 80 endpoints. Similarly, niche data like Hyperliquid positions or detailed order book L3 data may be excluded from Startup. In total ~20 endpoints (to reach 100) are gated. For instance, metrics derived from in-depth UTXO analysis (long-term holder supply, RHODL, etc.) likely require a higher tier because they mirror premium on-chain data from providers like Glassnode. If a Startup API call returns an “Upgrade required” error for an endpoint, it falls in this category.
	•	Not Provided by CoinGlass: A few metrics in the “Savaş Paneli” aren’t directly offered by CoinGlass’s API. We must source these from alternative free APIs:
	•	MVRV Z-Score (Market-Value-to-Realized-Value): Not in CoinGlass. Available via Glassnode Studio or API   (free tier for certain metrics) and CryptoQuant’s public charts .
	•	Miner Metrics: CoinGlass V4 has no mining or hash rate endpoints. Alternatives: Blockchain.com or Glassnode for hash rate, miner outflows, etc.
	•	Social/Sentiment Metrics: If needed (e.g. social volume, dev activity), use Santiment’s API (community edition) or IntoTheBlock’s free widgets. CoinGlass covers Fear & Greed Index but not, say, Twitter sentiment.
	•	Detailed Address Distribution: CoinGlass provides total active/new addresses  but not breakdown of whale addresses count. For whale address counts or holdings, use IntoTheBlock or Glassnode (which track addresses with ≥X BTC).
	•	Options Put/Call Ratio: Not explicitly in CoinGlass. Alternative: Deribit or free analytics sites for put/call ratios.

Summary: The CoinGlass Startup plan covers the majority of needed endpoints for our panel. High-level market, derivatives, ETF, and on-chain flow metrics are included , but a handful of granular on-chain metrics (related to long-term holder behavior, etc.) and any missing metrics will be fetched from free alternatives. Below, we detail each required metric’s source.

“Savaş Paneli” Metrics Overview (Daily, Weekly, Monthly)

The user’s “Savaş Paneli” organizes BTC metrics into three timeframes with themed sub-groups:
	•	DAILY (18 metrics) – Türev & Likidite (Derivatives & Liquidity), Spot & Kurumsal Akış (Spot & Institutional Flow), Momentum & Aşırılık (Momentum & Extremes). Daily metrics track short-term market activity and sentiment (e.g. open interest, funding, exchange flows, technical oscillators).
	•	WEEKLY (18 metrics) – Smart Money & Yapı (Smart Money & Market Structure). Weekly metrics focus on intermediate-term trends, including on-chain holder behavior (“smart money”) and structural indicators of market health (network usage, market composition).
	•	MONTHLY (15 metrics) – Cycle & Değerleme (Cycle & Valuation). Monthly metrics assess where BTC stands in larger market cycles and valuation models, using long-term indicators (e.g. stock-to-flow, halving-cycle signals, on-chain cycle extremes).

Each metric from these categories is listed in the tables below with its data source details. We include the metric name, the CoinGlass API endpoint (if available), example query parameters, Startup plan availability, any alternative source (if needed), and notes (e.g. special requirements or issues).

Daily Metrics – Derivatives & Liquidity (Türev & Likidite)

These six daily metrics capture leverage and liquidity conditions in the BTC market, mostly via CoinGlass futures data and on-chain exchange data:

Metric
CoinGlass Endpoint (Method)
Params Example
Startup Access
Alternative Source
Notes
Total Futures Open Interest (aggregate USD value of BTC open contracts)
/api/futures/openInterest/aggregated-history get
symbol=BTC, interval=1d, currency=USD
✓ Yes (Startup)
– (CryptoQuant for similar chart)
Use 1d interval for latest daily OI. Shows market leverage; accessible on Startup plan.
BTC Funding Rate (Global Avg) (avg perpetual funding % per day)
/api/futures/fundingRate/oi-weighted-history get or /api/futures/fundingRate/history for specific exchange
symbol=BTC, interval=1d (OI-weighted global)
✓ Yes
– (e.g. alternative: API by exchange if needed)
OI-weighted average funding rate across exchanges . Startup plan covers global funding data.
Long/Short Ratio (Global) (global long vs short account ratio)
/api/futures/longShortRatio/global-account-ratio get
symbol=BTC (may return current ratio or timeseries)
✓ Yes
– (Binance offers its own L/S ratio API)
CoinGlass global long-short account ratio accessible (may be instantaneous value). Use for sentiment (crowd leverage positioning).
Liquidations (24h) (total futures liquidations last 24h, USD)
/api/futures/liquidation/coin-history get (Coin Liquidation History)
symbol=BTC, interval=1d
✓ Yes
– (Coinglass UI or Coinalyze for ref)
CoinGlass provides BTC liquidation history . Sum of long/short liquidations in past day indicates volatility.
Exchange Reserves (BTC) (total BTC held on exchanges)
/api/onChain/exchangeBalance/chart get
symbol=BTC (all exchanges aggregate)
✓ Yes
CryptoQuant API (All Exchanges Reserve)
CoinGlass “Exchange Balance Chart” shows total BTC on exchanges . High reserves imply high available liquidity; falling reserves signal accumulation.
Stablecoin Supply (Total) (aggregate market cap of top stablecoins)
/api/indicator/StableCoin-MarketCap-History get
(interval 1d implicit)
✓ Yes
Alternative: CoinGecko (sum of USDT, USDC etc)
CoinGlass tracks total stablecoin market cap history . Indicates crypto liquidity; accessible on Startup.

Sources: CoinGlass API Futures docs  , On-chain exchange balance docs . Stablecoin data listed in CoinGlass indicators . All above endpoints are available to Hobbyist/Startup plans (no upgrade needed)  .

Daily Metrics – Spot & Institutional Flow (Spot & Kurumsal Akış)

These daily metrics track spot market activity and institutional money flows into BTC:

Metric
CoinGlass Endpoint (Method)
Params Example
Startup Access
Alternative Source
Notes
Exchange Net Flow (24h) (BTC net inflow/outflow to exchanges)
/api/futures/takerBuySell/coin-netflow get
symbol=BTC, interval=1d (net change)
✓ Yes
CryptoQuant (Exchange Netflow chart)
CoinGlass “Coin NetFlow” returns net BTC flow to exchanges . Negative = net outflow (hodling), positive = inflow (selling pressure).
Coinbase Premium Index (Coinbase vs global price spread)
/api/indicator/coinbase-premium-index get
symbol=BTC
✓ Yes
CryptoQuant (Coinbase Premium)
Measures US institutional buying power – positive premium means Coinbase price > others . Included in Startup plan.
Grayscale GBTC Premium (% GBTC vs NAV)
/api/etf/grayscale/premium-history get
(no symbol needed for GBTC)
✗ Locked (Std+)
Alternative: Glassnode or Ycharts (GBTC premium)
GBTC premium history may require Standard plan. If unavailable, use free sources for GBTC discount. Indicates institutional sentiment.
Bitcoin ETF Flows (weekly net asset flows into BTC ETFs)
/api/bitcoin/etf/flows-history get (use interval=1w for weekly)
interval=1w, limit=52
✓ Yes (Startup)
– (ETF data unique to CoinGlass)
CoinGlass tracks global Bitcoin ETF fund flows . Use weekly data to gauge institutional inflows/outflows. Startup plan includes this pioneering dataset.
Whale Transfer Volume (BTC moved in large txs, past 24h)
/api/onChain/whaleTransfer get
symbol=BTC
✓ Yes
Whale Alert API (free, limited)
CoinGlass “Whale Transfer” lists large on-chain transactions . Could sum volumes > certain threshold. Alternative: Whale Alert for broad large-TX tracking.
Bitcoin Dominance (% BTC of total crypto market cap)
/api/indicator/bitcoin-dominance get
(no params, global metric)
✓ Yes
CoinGecko API (global dominance)
BTC dominance is provided by CoinGlass . Useful to see if capital is rotating into altcoins. Startup accessible.

Notes: Grayscale Premium is one metric likely requiring a higher plan or external source – others are available in Startup. For example, GBTC premium data on CoinGlass might be limited; if so, one can get the premium from public sources (Grayscale reports or financial sites). The Coinbase Premium Index and net flow are explicitly part of CoinGlass’s indicator set  . Whale transfers are listed under on-chain transactions  (CoinGlass may not sum them, so external processing needed). Bitcoin dominance and ETF flows are readily accessible  .

Daily Metrics – Momentum & Extremes (Momentum & Aşırılık)

These daily metrics include technical momentum indicators and gauges of extreme market sentiment or positioning:

Metric
CoinGlass Endpoint (Method)
Params Example
Startup Access
Alternative Source
Notes
14-Day RSI (Relative Strength Index)
/api/indicator/futures/pair-rsi get or /api/indicator/futures/coin-rsi-list
symbol=BTC, interval=1d, period=14
✓ Yes
Compute via TA on price (Coingecko OHLC)
CoinGlass offers RSI for futures pairs . If needed, can calculate from daily price. Indicates momentum (overbought >70, oversold <30).
MACD (Moving Avg Conv./Div.) (12-26 day MACD on BTC price)
/api/indicator/futures/macd get
symbol=BTC, interval=1d
✓ Yes
Compute via TA library on price
CoinGlass provides MACD values . Use histogram or signal crossover for momentum shifts.
Crypto Fear & Greed Index (daily sentiment score)
/api/indicator/crypto-fear-greed-index get
(usually returns latest daily index)
✓ Yes (Startup)
Alternative.me free API
CoinGlass integrates the Fear & Greed Index . Ranges 0 (extreme fear) to 100 (extreme greed). Also freely available from alternative.me (no API key needed).
Futures vs Spot Volume Ratio (daily futures volume / spot volume)
/api/indicator/futures-vs-spot-volume-ratio get
symbol=BTC, interval=1d
✗ Likely Locked
Compute from exchange volumes (CoinGecko API)
A high ratio indicates excessive leverage vs spot. CoinGlass lists this metric , but if locked on Startup, we can calculate manually using total futures volume (sum of exchanges via CoinGlass or Coinalyze) divided by spot volume.
24h Spot Trading Volume (USD volume on major exchanges)
No direct endpoint (derived)
–
✓ Yes (via markets API)
CoinGecko API (24h volume)
CoinGlass /api/spot/coins-markets gives 24h volume for BTC . This gauges market activity momentum. CoinGecko free API is an easy alternative .
Bitfinex Margin Long/Short (ratio of BTC longs vs shorts on Bitfinex)
/api/indicator/bitfinex-margin-long-short get
(no params, specific to BTC)
✓ Yes
Bitfinex API (public stats)
CoinGlass tracks Bitfinex margin position data . An extreme spike in this ratio can signal retail leverage extremes. Startup plan supports this.

Most of these momentum/extreme indicators are accessible on Startup. The Futures vs Spot Volume Ratio might require Standard plan (if considered a premium metric); if so, we can approximate it externally. The Fear & Greed Index is included in CoinGlass’s “macro indicators”  and is also freely accessible elsewhere, ensuring no data gap. RSI/MACD are technical indicators CoinGlass computes for convenience , but they could also be calculated within our system using price data if needed (no plan restriction on calculating your own indicators).

Weekly Metrics – Smart Money & Market Structure (Smart Money & Yapı)

Weekly metrics (18 total) are split between Smart Money indicators (whales, long-term holders) and Market Structure indicators (network and market composition). These are typically observed week-over-week to smooth out noise.

Smart Money Indicators (Weekly)
Metric
CoinGlass Endpoint (Method)
Params Example
Startup Access
Alternative Source
Notes
Long-Term Holder Supply (total BTC held by long-term holders)
/api/indicator/bitcoin-long-term-holder-supply get
(no params, BTC-specific)
✗ Locked (Std)
Glassnode API (LTH Supply)
Indicates “smart money” holdings. Likely locked on CoinGlass (on-chain analytic). Glassnode provides this metric (requires at least free tier login).
Long-Term Holder SOPR (LTH Spent Output Profit Ratio)
/api/indicator/bitcoin-long-term-holder-sopr get
(no params)
✗ Locked
Glassnode (LTH-SOPR)
LTH SOPR <1 implies long-term holders selling at a loss (potential bottom signal). Probably not available on Startup; Glassnode or CryptoQuant offer SOPR metrics .
Whale Index (CoinGlass Whale Index for futures)
/api/indicator/whale-index get
symbol=BTC, interval=1w
✓ Yes
– (unique to CoinGlass)
The Whale Index tracks large traders’ impact . Provided by CoinGlass (Startup). Helps gauge whale activity in derivatives.
Top Traders Long/Short Ratio (aggregated top accounts positioning)
/api/futures/longShortRatio/top-account-ratio-history get
symbol=BTC, interval=1w
✓ Yes
– (exchange-specific alternatives)
Shows ratio of long vs short among top traders . CoinGlass provides historical series. A proxy for smart money sentiment on weekly scale.
Reserve Risk (cycle confidence of long-term holders)
/api/indicator/bitcoin-reserve-risk get
(no params)
✗ Locked
Glassnode (Reserve Risk)
Reserve Risk indicates risk/reward based on HODLer conviction. CoinGlass lists it but it’s likely gated. Glassnode publishes Reserve Risk charts (free view).
RHODL Ratio (Risk-adjusted HODL waves ratio)
/api/indicator/bitcoin-rhodl-ratio get
(no params)
✗ Locked
Glassnode (via research charts)
RHODL Ratio compares short-term vs long-term HODLer wealth (signals cycle peaks). On CoinGlass (likely higher plan). Use Glassnode’s community data if needed.
Whale Transaction Count (weekly count of $1M+ BTC transfers)
No direct endpoint (whaleTransfer gives list)
–
✓ (partial)
IntoTheBlock (Large TX Count)
We can count large txs from daily whaleTransfer data over a week. Alternatively, IntoTheBlock provides large transaction counts (% of volume by whales). Useful to see smart money movement.
BTC Exchange Balance % (percent of supply on exchanges)
Derived from Exchange Assets /api/onChain/exchangeAssets get
–
✓ Yes
Glassnode (Exchange Balance %)
CoinGlass “Exchange Assets” lists BTC holdings per exchange . From this, weekly average % of total supply on exchanges can be computed. Declining supply on exchanges signals accumulation by strong hands.
Bitcoin Active Addresses (Weekly avg)
/api/indicator/bitcoin-active-addresses get
(no params)
✓ Yes
Glassnode (active addrs), Santiment API
Active addresses (weekly average) measures network activity. CoinGlass provides this on-chain metric . Should be accessible (basic on-chain data). Also available via Glassnode’s free tier or Santiment for cross-check.
Smart Money notes: Many of these metrics come from deep on-chain analysis and might be locked on Startup. In particular, LTH Supply, LTH SOPR, Reserve Risk, RHODL are advanced Glassnode-like metrics and likely require an upgraded plan. We will integrate alternative data for those: e.g. use Glassnode’s public charts or CryptoQuant’s free metrics (CryptoQuant offers LTH SOPR and Exchange Reserve metrics free on their site) . Simpler metrics like Active Addresses or Whale Index are available on Startup (active addrs and whale index are explicitly listed and likely included)  . For Top trader ratio, CoinGlass directly provides it without extra cost .

Market Structure Indicators (Weekly)

Metric
CoinGlass Endpoint (Method)
Params Example
Startup Access
Alternative Source
Notes
New Addresses (Weekly) (new BTC addresses created)
/api/indicator/bitcoin-new-addresses get
(no params)
✓ Yes
Glassnode (New Address Count)
Tracks network growth. CoinGlass provides new addresses count . Startup accessible (basic on-chain). Weekly average smooths daily volatility.
Futures Basis (Annualized) (CME/major exchange futures basis %)
/api/indicator/futures-basis get
symbol=BTC, interval=1w
✓ Yes
Alternative: CME data via Quandl
CoinGlass gives futures basis history (difference between futures and spot). Indicates market structure (contango vs backwardation). Used weekly for trend (premium or discount of futures).
Options Put/Call Ratio (open interest put/call)
Not in CoinGlass
–
– (N/A)
Deribit API or gvol.io (free charts)
Measures structure of options market sentiment. Since CoinGlass lacks a direct endpoint, we can query Deribit’s OI data to calculate the ratio. Useful for weekly insight into hedging vs speculation.
Altcoin Season Index (whether alts outperform BTC)
/api/indicator/altcoin-season-index get
(no params)
✓ Yes
Blockchain Center (public index)
CoinGlass provides Altcoin Season Index . Helps understand market structure (dominance of BTC vs alts). Likely accessible on Startup (it’s a formula based on 90-day performance).
BTC Correlation with S&P500 (weekly correlation)
/api/indicator/bitcoin-correlations get
(no params, returns multi-asset correlations)
✗ Locked?
Alternative: CoinMetrics free API
CoinGlass lists Bitcoin correlations (probably with equities, gold, etc) . If not available on Startup, use CoinMetrics or Yahoo Finance to compute BTC–S&P correlation over 30d/90d. Indicates macro structure influence.
Net Unrealized P/L (NUPL) (% of market in profit minus loss)
/api/indicator/bitcoin-net-unrealized-pnl get
(no params)
✗ Locked
Glassnode (NUPL chart)
NUPL is a classic on-chain metric for market structure (greed vs fear). CoinGlass has it , but possibly restricted. We can source from Glassnode (they share NUPL in insights) or calculate from realized cap and market cap if needed.
BTC Market Cap vs Realized Cap (MVRV)
Not in CoinGlass (no direct MVRV endpoint)
–
– (N/A)
Glassnode (MVRV-Z) , CryptoQuant
MVRV Z-Score is a known market valuation structure metric (distance between market and realized value). Since CoinGlass doesn’t offer it directly, use Glassnode’s free metric or CryptoQuant’s published data .
Exchange Stablecoin Ratio (SSR) (BTC market cap / stablecoin cap)
Derived (from BTC market cap and stablecoin cap)
–
✓ Yes (computed)
CryptoQuant (SSR)
SSR indicates buying power from stablecoins. Not a direct endpoint, but can compute using CoinGlass’s BTC market cap (price * supply) and stablecoin market cap . Weekly monitoring of this ratio shows structural liquidity.

Market Structure notes: Most of these focus on the broader context in which BTC operates each week. New addresses and NUPL give insight into on-chain structure (adoption and profit landscape); futures basis and put/call ratio reveal derivatives market structure. Altcoin Season Index and correlations situate BTC in the multi-asset landscape. We’ll fetch alternative data for the ones CoinGlass doesn’t provide to Startup (e.g. correlation and MVRV). Many on-chain structure metrics (NUPL, etc.) overlap with cycle indicators, but monitoring weekly can foreshadow cycle shifts.

Monthly Metrics – Cycle & Valuation (Döngü & Değerleme)

Monthly (15 metrics) metrics evaluate BTC’s position in long-term cycles and whether it’s over- or undervalued relative to historical models. These include a range of popular on-chain and technical cycle indicators:

Metric
CoinGlass Endpoint (Method)
Params Example
Startup Access
Alternative Source
Notes
Puell Multiple (Miners’ revenue cycle indicator)
/api/indicator/puell-multiple get
(no params)
✓ Yes (likely)
– (Glassnode publishes chart)
CoinGlass provides Puell Multiple which signals miner profitability extremes (high values at tops, low at bottoms). Included in long-term indicators (Startup).
Stock-to-Flow Model (BTC price vs S2F fair value)
/api/indicator/stock-to-flow-model get
(no params)
✓ Yes
–
CoinGlass integrates the S2F model (popular but controversial). We can retrieve the S2F “predicted” price and compare to actual.
Pi Cycle Top Indicator (MA cross-based top signal)
/api/indicator/pi-cycle-top-indicator get
(no params)
✓ Yes
–
CoinGlass provides Pi Cycle Top indicator . It flags cycle tops when certain short/long MAs cross. Good for valuation peak check.
Golden Ratio Multiplier (MA multiples valuation tool)
/api/indicator/golden-ratio-multiplier get
(no params)
✓ Yes
–
A long-term technical model using Fibonacci multiples of moving averages (CoinGlass endpoint available ). Indicates overheated conditions when price exceeds certain multiples.
200-Week Moving Avg Heatmap (color-coded deviation from 200W MA)
/api/indicator/200-week-moving-avg-heatmap get
(no params)
✓ Yes
– (LookIntoBitcoin chart)
CoinGlass includes the famous 200W MA Heatmap . Shows how far below/above 200-week MA the price is, with color indicating momentum of change. Key for cycle bottoms (price near or below 200W MA).
Two-Year MA Multiplier (price vs 2-year MA band)
/api/indicator/tow-year-ma-multiplier get
(no params)
✓ Yes
–
CoinGlass provides 2-Year MA Multiplier (price vs 2yr MA and 5x 2yr MA). Historically, great accumulation (below 2yr MA) and selling (above 2yr*5) zones.
AHR 999 (Analyst “Ahır” 999-day indicator)
/api/indicator/ahr999 get
(no params)
✓ Yes
–
An indicator (popular in some communities) comparing price to 3-year moving averages . CoinGlass supports it. Used to identify cheap vs expensive zones.
Bitcoin Rainbow Chart (logarithmic regression bands)
/api/indicator/bitcoin-rainbow-chart get
(no params)
✓ Yes
– (BlockchainCenter chart)
The Rainbow Chart bands (from “Fire sale” to “Bubble”) are provided by CoinGlass . Great visual valuation tool. Startup plan includes this fun but insightful metric.
Bitcoin Profitable Days (% of days BTC price was below today’s)
/api/indicator/bitcoin-profitable-days get
(no params)
✓ Yes
–
CoinGlass offers “% of Bitcoin days profitable” . If this is 99%+, price is near ATH (expensive); if ~50%, we’re near cycle lows. Always accessible (no heavy data needed).
Bitcoin Bubble Index (distance from historical trend, custom index)
/api/indicator/bitcoin-bubble-index get
(no params)
✓ Yes
–
A CoinGlass index attempting to quantify bubbles . Likely based on deviations from growth trends. Useful for valuation; available on Startup.
Reserve Risk (repeated) – also listed under weekly Smart Money, but evaluated monthly for cycle lows
/api/indicator/bitcoin-reserve-risk get
–
✗
Glassnode
At monthly scale, Reserve Risk highlights major cycle bottoms (when risk is very low). If locked in API, we’ll rely on external data for analysis.
Net Unrealized P/L (NUPL) (repeated) – evaluated monthly for cycle phase
/api/indicator/bitcoin-net-unrealized-pnl get
–
✗
Glassnode
NUPL is a core valuation metric (high values ~ greed, low ~ capitulation). If CoinGlass restricts it on Startup, use Glassnode’s community data.
MVRV Z-Score (market vs realized cap z-score)
No direct endpoint
–
–
Glassnode (MVRV-Z)
We will manually include MVRV-Z as it’s a respected valuation metric: when far above 0 (esp. >7-8) indicates overheated market (red zone); below 0 (green zone) indicates undervaluation. Not in CoinGlass API.
Altcoin Season Index (if not used weekly) – long-term view
/api/indicator/altcoin-season-index get
–
✓ Yes
Blockchain Center
We might include this here or weekly, but it can show if multi-year cycle is BTC-dominant or alt-dominant. Already covered under weekly structure.
Bitcoin Dominance (repeated) – long-term trend
/api/indicator/bitcoin-dominance get
–
✓ Yes
CoinGecko API
Already in daily flows; on a monthly scale, its trend reflects cycle phases (e.g. BTC dominance tends to peak in bear markets). Monitored but not a unique metric for monthly.
Cycle/Valuation notes: Almost all these long-term indicators are provided by CoinGlass and do not appear to be restricted by plan – they are largely based on public data or known formulas (CoinGlass added them for user convenience) . The Startup plan should allow querying them (they are likely counted in the ~80 endpoints). For example, Fear & Greed, Rainbow, S2F, etc., are explicitly part of the API reference and marked available to all plans  . Metrics that involve proprietary on-chain data (Reserve Risk, NUPL) we have flagged as needing external sources if they fail on Startup. In practice, even without API access, one can use Glassnode’s free Studio to fetch values or look at published charts for those monthly values. The MVRV Z-Score, not in CoinGlass, will rely on Glassnode (it’s well-known and often free in blogs) .

Technical Architecture Proposal

To integrate all the above metrics into a unified, automated CLI dashboard (btc command), we propose the following architecture and workflow:
	•	Maintain Repository Structure: We will extend the existing coinglass-v4-batch3 Python project without breaking it. Existing modules for CoinGlass API calls will be reused. All new data fetching logic will reside in new modules/adapters to keep separation of concerns, while using similar patterns as the current repo.
	•	New Modules/Adapters: Introduce dedicated adapters for any external sources needed:
	•	E.g. glassnode_api.py for fetching metrics like MVRV or LTH-Supply (using their REST endpoints or parsing their public CSVs).
	•	cryptoquant_api.py for metrics like exchange netflows or SOPR if CoinGlass lacks them (CryptoQuant offers a free API for some metrics).
	•	These adapters will handle authentication (if any) and return data in a normalized format. Each adapter will be clearly named and documented (e.g., functions get_glassnode_mvrv() or get_cryptoquant_active_addresses()).
	•	For CoinGlass, continue using the existing client or HTTP wrapper in the repo. We might add new functions in the CoinGlass data module for endpoints not yet covered (e.g., get_altseason_index() if not already present).
	•	Data Fetching & Caching: When the btc CLI command is invoked, the program will fetch all required metrics in parallel or sequentially with efficient reuse of data:
	•	Many CoinGlass endpoints allow batch retrieval (e.g., we can request multiple symbols or all exchanges at once). But since we mostly need BTC-specific metrics, calls are separate.
	•	Use batch requests where possible (CoinGlass has high rate limits for Startup: 80/min ). We can comfortably fetch ~50 endpoints in one run. Still, group related metrics to avoid redundant calls.
	•	Caching: Implement an in-memory or disk cache (SQLite or JSON file) to store recent results. Because most metrics update daily or weekly, caching prevents unnecessary API calls if the user reruns btc multiple times a day. For example, we could cache daily metrics for 1 hour and weekly/monthly metrics for 1 day. A simple SQLite DB or even a JSON file with timestamps can suffice. This reduces API usage and ensures we don’t hit rate limits.
	•	We will also log each API call’s result (or any errors) for debugging and auditing, possibly in a logs/ file with timestamps.
	•	Integration in CLI: The btc command will orchestrate the data collection and display:
	•	It will call CoinGlass API for all metrics that are available (using the API key from config).
	•	For each metric group (Daily/Weekly/Monthly), if any metric is missing from CoinGlass (or locked), the CLI will automatically fetch from the alternative adapter. For instance, if the CoinGlass response for LTH Supply indicates an error (plan locked), the code will fall back to glassnode_api.get_lth_supply().
	•	The results will be compiled into a structured Python dict (or OrderedDict) with keys daily, weekly, monthly, each containing sub-dicts for each metric name and value. This will facilitate easy output in both JSON and text.
	•	Output Formatting (JSON + Text): The CLI will produce a human-readable text report organized by the metric groups, and optionally a machine-readable JSON:
	•	The text output will use clear section headers for DAILY, WEEKLY, MONTHLY. For example:

DAILY Metrics – Derivatives & Liquidity:
• Futures Open Interest: $10.5B (↑2% vs yesterday)
• Funding Rate (avg): 0.0100% (positive funding, bulls paying) … 
...
WEEKLY Metrics – Smart Money & Structure:
• Long-Term Holder Supply: 13.2M BTC (all-time high) … 
...

Each bullet will include the metric name and the value, plus perhaps a brief context or trend arrow if we compute change (we can store previous values in cache to compute WoW or DoD changes).

	•	Use indentation or bullet points as above for readability (3-5 sentences per section is not needed since it’s a list format, but we will ensure explanations are concise).
	•	For the JSON output, we have options:
	1.	Dual output: Print the text report for the user to read, and print a JSON string to stdout or to a file. We could, for instance, print the JSON first (so it can be piped to other tools) followed by the formatted text for human reading. Or vice versa.
	2.	Alternatively, provide a command flag like btc --json to output only JSON. But the prompt suggests the user wants both in one go.
	3.	We can organize the JSON with the same structure as the panel:

{
  "daily": {
    "derivatives_liquidity": {
      "open_interest": 10500000000,
      "funding_rate": 0.0001,
      ... 
    },
    "spot_institutional": { ... },
    "momentum_extremes": { ... }
  },
  "weekly": { ... },
  "monthly": { ... }
}

This JSON could be written to a file (e.g. btc_dashboard.json) every run, and the path indicated in the output.

	•	Why JSON? So that the data can be programmatically ingested elsewhere (for example, if the user wants to feed it to a web dashboard or further analysis). The text is for immediate viewing.
	•	We will ensure the text aligns with the JSON (same values). We’ll also include units (%, BTC, USD) in text but not in JSON numeric values.

	•	Sectioning and Titles: Each metric sub-group will be clearly separated with a title line. E.g. ===== DAILY: Derivatives & Liquidity ===== or a simpler Daily – Derivatives & Liquidity: as a bold line. This improves readability. The user specifically requested grouping by those subcategories, so we will do so in output as well.
	•	Cronjob & Automation: To keep data up-to-date, if needed, a cronjob can run the btc command daily/weekly and output to a file or push notifications. The architecture supports this as the CLI is fully automated. We recommend:
	•	A daily cron at, say, 00:00 UTC to update daily metrics and store JSON results.
	•	A weekly cron (perhaps every Monday 00:00) for weekly metrics, and monthly on the 1st of each month for monthly. (Our code will fetch weekly metrics any day it’s run, but the values only change once a week significantly – we could decide to only print weekly on certain days to avoid confusion).
	•	Logging these cron runs in a log file for history.
	•	Error Handling & Logging: If an API call fails (network issue or rate limit), the system will log the error and either retry (with exponential backoff) or report “N/A” for that metric in output. This way the CLI never fully breaks; it will deliver partial data with clear indication of any missing pieces. Since Startup plan has generous limits (80 calls/min) , hitting limits is unlikely if we structure calls well. But logging to file with timestamps and any API error messages is good practice.
	•	Extensibility: The modular design (separate adapters for alt sources and clearly delineated metric definitions) will make it easy to add/remove metrics. For instance, if the user later decides to add “Hash Rate” as a metric, we can add a Hashrate adapter (fetch from Blockchain.com API) and include it in the appropriate category (likely Daily or Weekly Momentum).

Finally, we’ll leverage community resources and examples where helpful. Notably, an unofficial CoinGlass Python client exists , which demonstrates how to call various endpoints (open interest, funding, GBTC, etc.). We can draw on its methods to ensure our queries and parameter usage are correct. Additionally, exploring open-source crypto CLI tools (like CoinGecko’s or others on GitHub) can inspire our output formatting. Reddit discussions indicate that many developers use CoinGecko for free price data and Glassnode for on-chain stats in personal projects  , validating our approach of combining sources.

In summary, this architecture will result in a robust CLI that, upon running btc, fetches all defined metrics (from CoinGlass wherever possible, supplemented by free alternatives), then outputs a nicely formatted report segmented into Daily/Weekly/Monthly with JSON data ready for any further integration. This fulfills the goal of a fully automated BTC dashboard using CoinGlass Startup as the backbone and plugging any gaps with other free data sources.


————————————————————————————————————————————————————————————————————————————————————————————————————————————————
