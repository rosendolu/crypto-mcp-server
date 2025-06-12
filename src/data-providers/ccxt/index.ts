import { LOG_DIR } from '@/constant';
import {
    BalanceAsset,
    BalanceInfo,
    BookTicker,
    CancelResult,
    Candlestick,
    DustLog,
    ExchangeConfig,
    ExchangeId,
    ExchangeInstance,
    Order,
    OrderBook,
    OrderResult,
    OrderSide,
    OrderStatus,
    OrderType,
    PrevDayStats,
    SUPPORTED_EXCHANGES,
    TickerData,
    Trade,
} from '@/types/ccxt.types';
import logger from '@/utils/logger';
import ccxt from 'ccxt';
import dayjs from 'dayjs';
import fs from 'fs';
import path from 'path';

// Dynamically populate SUPPORTED_EXCHANGES from ccxt.exchanges
SUPPORTED_EXCHANGES.length = 0;
SUPPORTED_EXCHANGES.push(...ccxt.exchanges);

function getEnv(key: string): string | undefined {
    return process.env[key] || undefined;
}

function getExchangeConfig(id: ExchangeId): ExchangeConfig | null {
    const upperId = id.toUpperCase();
    const apiKey = getEnv(`${upperId}_API_KEY`);
    const secret = getEnv(`${upperId}_SECRET`);
    if (apiKey && secret) {
        return {
            id,
            apiKey,
            secret,
        };
    }
    return null;
}

function createExchangeInstance(config: ExchangeConfig): ExchangeInstance {
    const ccxtClass = (ccxt as any)[config.id];
    if (!ccxtClass) throw new Error(`CCXT does not support exchange: ${config.id}`);
    const options: any = {
        apiKey: config.apiKey,
        secret: config.secret,
    };
    if (process.env.LOG_LEVEL === 'debug') {
        options.verbose = true;
    }
    return new ccxtClass(options);
}

// Initialize all supported exchanges
const availableConfigs: ExchangeConfig[] = SUPPORTED_EXCHANGES.map(getExchangeConfig).filter(
    (c): c is ExchangeConfig => !!c
);

if (availableConfigs.length === 0) {
    logger.error('No valid exchange API credentials found in environment variables.');
    throw new Error('No valid exchange API credentials found. Please check your .env configuration.');
}

let exchangeInstances: Partial<Record<ExchangeId, ExchangeInstance>> = {};
for (const config of availableConfigs) {
    try {
        exchangeInstances[config.id] = createExchangeInstance(config);
        logger.info('Initialized exchange: %s', config.id);
    } catch (err) {
        logger.error('Failed to initialize exchange %s: %s', config.id, err);
    }
}

let currentExchangeId: ExchangeId = availableConfigs[0]?.id || 'binance';

export function getExchange(id?: ExchangeId): ExchangeInstance {
    let useId = id;
    if (!useId) {
        logger.warn('No exchange specified, defaulting to binance.');
        useId = 'binance';
    }
    if (!exchangeInstances[useId]) {
        throw new Error(`Exchange ${useId} is not configured or failed to initialize.`);
    }
    currentExchangeId = useId;
    return exchangeInstances[useId]!;
}

export function getCurrentExchangeId(): ExchangeId {
    return currentExchangeId;
}

export function getAvailableExchanges(): ExchangeId[] {
    return Object.keys(exchangeInstances) as ExchangeId[];
}

// Utility: Check all supported exchanges for API key/secret config
export function checkExchangeConfigs(): Array<{ id: string; name: string; ready: boolean; error?: string }> {
    return SUPPORTED_EXCHANGES.map(id => {
        const config = getExchangeConfig(id);
        if (config) {
            try {
                const ccxtClass = (ccxt as any)[id];
                const name = ccxtClass ? new ccxtClass().name : id;
                return { id, name, ready: true };
            } catch (e) {
                return { id, name: id, ready: false, error: String(e) };
            }
        } else {
            return { id, name: id, ready: false, error: 'Missing API key/secret' };
        }
    });
}

/**
 * Adapts the trading pair symbol to the correct format for each supported exchange.
 * - binance, okx, kucoin, bybit, bitget, mexc, huobi: 'BASE/QUOTE' (uppercase, slash)
 * - gate: 'BASE_QUOTE' (uppercase, underscore)
 * - For all others: 'BASE/QUOTE' (uppercase, slash)
 * See: https://docs.ccxt.com/#/?id=symbols-and-market-ids
 */
export function adaptSymbolForExchange(symbol: string, exchangeId?: ExchangeId): string {
    if (!symbol || !exchangeId) return symbol;
    // Normalize input: accept BTC/USDT, btc/usdt, BTC_USDT, btc_usdt, BTCUSDT
    let base = '',
        quote = '';
    const match = symbol.match(/^(\w+)[_\/-]?(\w+)$/i);
    if (match) {
        base = match[1];
        quote = match[2];
    } else {
        return symbol;
    }
    switch (exchangeId) {
        case 'binance':
        case 'okx':
        case 'kucoin':
        case 'bybit':
        case 'bitget':
        case 'mexc':
        case 'huobi':
        case 'gate':
            // CCXT expects 'BASE_QUOTE' (uppercase, slash)
            return `${base.toUpperCase()}_${quote.toUpperCase()}`;
        default:
            // Default to 'BASE/QUOTE' (uppercase, slash)
            return `${base.toUpperCase()}/${quote.toUpperCase()}`;
    }
}

// Utility to normalize symbol to BASE/QUOTE uppercase format
// e.g., ETH/USDT, BTC/USDT
function normalizeSymbol(symbol: string): string {
    if (!symbol) return symbol;
    return symbol.toUpperCase();
}

// Market Data
/**
 * Get current price for all/specified symbols
 */
export async function prices(symbol?: string, exchangeId?: ExchangeId): Promise<TickerData[] | TickerData | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called prices with params: %j', { symbol, exchangeId });
        if (symbol) {
            const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
            const normalized = normalizeSymbol(adaptedSymbol);
            const ticker = await exchange.fetchTicker(normalized);
            logger.info('Fetched ticker for %s: %j', normalized, ticker);
            logger.debug('prices result: %j', ticker);
            return {
                symbol: ticker.symbol,
                price: Number(ticker.last),
                timestamp: ticker.timestamp,
            };
        } else {
            const tickers = await exchange.fetchTickers();
            logger.info('Fetched all tickers');
            logger.debug('prices result: %j', tickers);
            return Object.values(tickers).map((t: any) => ({
                symbol: t.symbol,
                price: Number(t.last),
                timestamp: t.timestamp,
            }));
        }
    } catch (error) {
        logger.error('Error fetching prices: %s', error);
        return null;
    }
}

/**
 * Get best bid/ask price for all/specified symbols
 */
export async function bookTickers(symbol?: string, exchangeId?: ExchangeId): Promise<BookTicker[] | BookTicker | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called bookTickers with params: %j', { symbol, exchangeId });
        if (symbol) {
            const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
            const ob = await exchange.fetchOrderBook(adaptedSymbol, 1);
            logger.info('Fetched book ticker for %s', adaptedSymbol);
            logger.debug('bookTickers result: %j', ob);
            return {
                symbol,
                bidPrice: ob.bids[0]?.[0] ?? 0,
                bidQty: ob.bids[0]?.[1] ?? 0,
                askPrice: ob.asks[0]?.[0] ?? 0,
                askQty: ob.asks[0]?.[1] ?? 0,
                timestamp: ob.timestamp,
            };
        } else {
            // CCXT does not have fetchBookTickers, iterate all symbols
            const markets = await exchange.loadMarkets();
            const symbols: string[] = Object.keys(markets);
            const results: BookTicker[] = [];
            for (const s of symbols) {
                try {
                    const adaptedSymbol = adaptSymbolForExchange(s, exchangeId);
                    const ob = await exchange.fetchOrderBook(adaptedSymbol, 1);
                    results.push({
                        symbol: s,
                        bidPrice: ob.bids[0]?.[0] ?? 0,
                        bidQty: ob.bids[0]?.[1] ?? 0,
                        askPrice: ob.asks[0]?.[0] ?? 0,
                        askQty: ob.asks[0]?.[1] ?? 0,
                        timestamp: ob.timestamp,
                    });
                } catch (e) {
                    logger.warn('Failed to fetch book ticker for %s: %s', s, e);
                }
            }
            logger.info('Fetched book tickers for all symbols');
            logger.debug('bookTickers result: %j', results);
            return results;
        }
    } catch (error) {
        logger.error('Error fetching book tickers: %s', error);
        return null;
    }
}

/**
 * Get order book (market depth) for a symbol
 */
export async function depth(symbol: string, exchangeId?: ExchangeId): Promise<OrderBook | null> {
    const exchange = getExchange(exchangeId);
    try {
        const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
        logger.debug('Called depth with params: %j', { symbol, adaptedSymbol, exchangeId });
        const ob = await exchange.fetchOrderBook(adaptedSymbol);
        logger.info('Fetched order book for %s', adaptedSymbol);
        logger.debug('depth result: %j', ob);
        return {
            symbol,
            bids: ob.bids,
            asks: ob.asks,
            timestamp: ob.timestamp,
        };
    } catch (error) {
        logger.error('Error fetching order book for %s: %s', symbol, error);
        return null;
    }
}

/**
 * Get 24hr price change statistics for all/specified symbols
 */
export async function prevDay(
    symbol?: string | false,
    exchangeId?: ExchangeId
): Promise<PrevDayStats[] | PrevDayStats | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called prevDay with params: %j', { symbol, exchangeId });
        if (symbol && typeof symbol === 'string') {
            const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
            const stats = await exchange.fetchTicker(adaptedSymbol);
            logger.info('Fetched 24hr stats for %s', adaptedSymbol);
            logger.debug('prevDay result: %j', stats);
            return {
                symbol: stats.symbol,
                priceChange: Number(stats.change),
                priceChangePercent: Number(stats.percentage),
                weightedAvgPrice: Number(stats.average),
                prevClosePrice: Number(stats.previousClose),
                lastPrice: Number(stats.last),
                lastQty: Number(stats.lastQty ?? 0),
                bidPrice: Number(stats.bid),
                askPrice: Number(stats.ask),
                openPrice: Number(stats.open),
                highPrice: Number(stats.high),
                lowPrice: Number(stats.low),
                volume: Number(stats.baseVolume),
                quoteVolume: Number(stats.quoteVolume),
                openTime: stats.openTime ?? 0,
                closeTime: stats.closeTime ?? 0,
                firstId: stats.firstId,
                lastId: stats.lastId,
                count: stats.count,
            };
        } else {
            const tickers = await exchange.fetchTickers();
            logger.info('Fetched 24hr stats for all symbols');
            logger.debug('prevDay result: %j', tickers);
            return Object.values(tickers).map((stats: any) => ({
                symbol: stats.symbol,
                priceChange: Number(stats.change),
                priceChangePercent: Number(stats.percentage),
                weightedAvgPrice: Number(stats.average),
                prevClosePrice: Number(stats.previousClose),
                lastPrice: Number(stats.last),
                lastQty: Number(stats.lastQty ?? 0),
                bidPrice: Number(stats.bid),
                askPrice: Number(stats.ask),
                openPrice: Number(stats.open),
                highPrice: Number(stats.high),
                lowPrice: Number(stats.low),
                volume: Number(stats.baseVolume),
                quoteVolume: Number(stats.quoteVolume),
                openTime: stats.openTime ?? 0,
                closeTime: stats.closeTime ?? 0,
                firstId: stats.firstId,
                lastId: stats.lastId,
                count: stats.count,
            }));
        }
    } catch (error) {
        logger.error('Error fetching 24hr stats: %s', error);
        return null;
    }
}

/**
 * Get candlestick (OHLCV) data for a symbol
 */
export async function candlesticks(
    symbol: string,
    interval: string,
    options?: object,
    exchangeId?: ExchangeId
): Promise<Candlestick[] | null> {
    const exchange = getExchange(exchangeId);
    try {
        const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
        logger.debug('Called candlesticks with params: %j', { symbol, adaptedSymbol, interval, options, exchangeId });
        const ohlcv = await exchange.fetchOHLCV(adaptedSymbol, interval, undefined, undefined, options);
        logger.info('Fetched candlesticks for %s %s', adaptedSymbol, interval);

        const result = ohlcv.map((c: any) => ({
            openTime: c[0],
            open: Number(c[1]),
            high: Number(c[2]),
            low: Number(c[3]),
            close: Number(c[4]),
            volume: Number(c[5]),
            closeTime: c[6] ?? 0,
            quoteAssetVolume: c[7] ?? 0,
            numberOfTrades: c[8] ?? 0,
            takerBuyBaseAssetVolume: c[9] ?? 0,
            takerBuyQuoteAssetVolume: c[10] ?? 0,
            symbol: adaptedSymbol,
            interval,
            exchangeId,
        }));
        const fileName = `${dayjs().format('YYYY-MM-DD_HHmmss')}_${symbol.replace(/[_\/]/g, '_')}_${
            exchangeId || getCurrentExchangeId()
        }.json`;
        const filePath = path.join(LOG_DIR, fileName);
        try {
            fs.writeFileSync(filePath, JSON.stringify(result, null, 2), 'utf-8');
            logger.debug('Wrote candlestick data to %s', filePath);
        } catch (err) {
            logger.error('Failed to write candlestick data to %s: %s', filePath, err);
        }

        return result;
    } catch (error) {
        logger.error('Error fetching candlesticks for %s: %s', symbol, error);
        return null;
    }
}

// Account Information
/**
 * Get account balance information
 */
export async function balance(exchangeId?: ExchangeId): Promise<BalanceInfo | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called balance with params: %j', { exchangeId });
        const bal = await exchange.fetchBalance();
        logger.info('Fetched account balance');
        const assets: BalanceAsset[] = Object.keys(bal.total)
            .filter(asset => Number(bal.total[asset]) > 0)
            .map(asset => ({
                asset,
                free: Number(bal.free[asset] ?? 0),
                used: Number(bal.used[asset] ?? 0),
                total: Number(bal.total[asset] ?? 0),
            }));
        logger.debug('balance result: %j', { assets, timestamp: bal.info?.updateTime || Date.now() });
        return {
            assets,
            timestamp: bal.info?.updateTime || Date.now(),
        };
    } catch (error) {
        logger.error('Error fetching account balance: %s', error);
        return null;
    }
}

/**
 * Get dust log (small asset conversion history)
 * Only supported on Binance, returns null for other exchanges
 */
export async function dustLog(exchangeId?: ExchangeId): Promise<DustLog[] | null> {
    const exchange = getExchange(exchangeId);
    if ((exchangeId || getCurrentExchangeId()) !== 'binance') {
        logger.warn('dustLog is only supported on Binance.');
        return null;
    }
    try {
        logger.debug('Called dustLog with params: %j', { exchangeId });
        if (typeof exchange.sapiGetAssetDribblet === 'function') {
            const result = await exchange.sapiGetAssetDribblet();
            logger.info('Fetched dust log');
            // Parse Binance response structure
            const logs: DustLog[] = (result?.userAssetDribbletLogVos || []).flatMap((log: any) =>
                (log.userAssetDribbletDetails || []).map((d: any) => ({
                    asset: d.asset,
                    amount: Number(d.amount),
                    serviceChargeAmount: Number(d.serviceChargeAmount),
                    operateTime: d.operateTime,
                    transferedAmount: Number(d.transferedAmount),
                    fromAsset: d.fromAsset,
                    toAsset: d.transferedAsset,
                    status: d.transStatus,
                }))
            );
            logger.debug('dustLog result: %s', typeof logs === 'object' ? JSON.stringify(logs) : logs);
            return logs;
        } else {
            logger.warn('Binance sapiGetAssetDribblet not available on this ccxt version.');
            return null;
        }
    } catch (error) {
        logger.error('Error fetching dust log: %s', error);
        return null;
    }
}

// Order Operations
/**
 * Place a limit buy order
 */
export async function buy(
    symbol: string,
    quantity: number,
    price: number,
    options: Partial<{ type: OrderType; icebergQty?: number }> = {},
    exchangeId?: ExchangeId
): Promise<OrderResult | null> {
    const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
    return placeOrder('buy', adaptedSymbol, quantity, price, options, exchangeId);
}

/**
 * Place a limit sell order
 */
export async function sell(
    symbol: string,
    quantity: number,
    price: number,
    options: Partial<{ type: OrderType; icebergQty?: number }> = {},
    exchangeId?: ExchangeId
): Promise<OrderResult | null> {
    const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
    return placeOrder('sell', adaptedSymbol, quantity, price, options, exchangeId);
}

/**
 * Place a market buy order
 */
export async function marketBuy(
    symbol: string,
    quantity: number,
    options: object = {},
    exchangeId?: ExchangeId
): Promise<OrderResult | null> {
    const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
    return placeOrder('buy', adaptedSymbol, quantity, undefined, { ...options, type: 'market' }, exchangeId);
}

/**
 * Place a market sell order
 */
export async function marketSell(
    symbol: string,
    quantity: number,
    options: object = {},
    exchangeId?: ExchangeId
): Promise<OrderResult | null> {
    const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
    return placeOrder('sell', adaptedSymbol, quantity, undefined, { ...options, type: 'market' }, exchangeId);
}

/**
 * General order placement method, supports advanced order parameters
 */
async function placeOrder(
    side: OrderSide,
    symbol: string,
    quantity: number,
    price?: number,
    options: Partial<{ type: OrderType; icebergQty?: number }> = {},
    exchangeId?: ExchangeId
): Promise<OrderResult | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called placeOrder with params: %j', { side, symbol, quantity, price, options, exchangeId });
        const type: OrderType = options.type || 'limit';
        const params: any = {};
        if (options.icebergQty) params.icebergQty = options.icebergQty;
        // Support stop/trigger/iceberg and other advanced params
        let order;
        if (type === 'market') {
            order = await exchange.createOrder(symbol, 'market', side, quantity, undefined, params);
        } else {
            order = await exchange.createOrder(symbol, type, side, quantity, price, params);
        }
        logger.info('Placed %s order: %j', side, order);
        return {
            orderId: String(order.id),
            symbol: order.symbol,
            status: order.status,
            type: order.type,
            side: order.side,
            price: Number(order.price),
            amount: Number(order.amount),
            filled: Number(order.filled),
            timestamp: order.timestamp,
            info: order.info,
        };
    } catch (error) {
        logger.error('Error placing %s order for %s: %s', side, symbol, error);
        return null;
    }
}

/**
 * Query order status
 */
export async function orderStatus(
    symbol: string,
    orderId: string,
    exchangeId?: ExchangeId
): Promise<OrderStatus | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called orderStatus with params: %j', { symbol, orderId, exchangeId });
        const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
        const order = await exchange.fetchOrder(orderId, adaptedSymbol);
        logger.info('Fetched order status for %s %s', adaptedSymbol, orderId);
        logger.debug('orderStatus result: %j', order);

        return {
            orderId: String(order.id),
            symbol: order.symbol,
            status: order.status,
            type: order.type,
            side: order.side,
            price: Number(order.price),
            amount: Number(order.amount),
            filled: Number(order.filled),
            remaining: Number(order.remaining),
            timestamp: order.timestamp,
            info: order.info,
        };
    } catch (error) {
        logger.error('Error fetching order status for %s %s: %s', symbol, orderId, error);
        return null;
    }
}

/**
 * Get all orders (active, canceled, completed)
 */
export async function allOrders(symbol: string, exchangeId?: ExchangeId): Promise<Order[] | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called allOrders with params: %j', { symbol, exchangeId });
        const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
        const orders = await exchange.fetchOrders(adaptedSymbol);
        logger.info('Fetched all orders for %s', adaptedSymbol);
        logger.debug('allOrders result: %j', orders);
        return orders.map((order: any) => ({
            orderId: String(order.id),
            symbol: order.symbol,
            status: order.status,
            type: order.type,
            side: order.side,
            price: Number(order.price),
            amount: Number(order.amount),
            filled: Number(order.filled),
            remaining: Number(order.remaining),
            timestamp: order.timestamp,
            info: order.info,
        }));
    } catch (error) {
        logger.error('Error fetching all orders for %s: %s', symbol, error);
        return null;
    }
}

/**
 * Get all open orders for specified/all symbols
 */
export async function openOrders(symbol?: string, exchangeId?: ExchangeId): Promise<Order[] | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called openOrders with params: %j', { symbol, exchangeId });
        let orders;
        if (!symbol) {
            orders = await exchange.fetchOpenOrders(undefined);
            logger.info('Fetched open orders for all symbols');
        } else {
            const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
            orders = await exchange.fetchOpenOrders(adaptedSymbol);
            logger.info('Fetched open orders for %s', adaptedSymbol);
        }
        logger.debug('openOrders result: %j', orders);
        return orders.map((order: any) => ({
            orderId: String(order.id),
            symbol: order.symbol,
            status: order.status,
            type: order.type,
            side: order.side,
            price: Number(order.price),
            amount: Number(order.amount),
            filled: Number(order.filled),
            remaining: Number(order.remaining),
            timestamp: order.timestamp,
            info: order.info,
        }));
    } catch (error) {
        logger.error('Error fetching open orders for %s: %s', symbol, error);
        return null;
    }
}

/**
 * Cancel a specific order
 */
export async function cancel(symbol: string, orderId: string, exchangeId?: ExchangeId): Promise<CancelResult | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called cancel with params: %j', { symbol, orderId, exchangeId });
        const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
        const result = await exchange.cancelOrder(orderId, adaptedSymbol);
        logger.info('Cancelled order %s for %s', orderId, adaptedSymbol);
        logger.debug('cancel result: %j', result);
        return {
            orderId: String(result.id),
            symbol: result.symbol,
            status: result.status,
            info: result.info,
        };
    } catch (error) {
        logger.error('Error cancelling order %s for %s: %s', orderId, symbol, error);
        return null;
    }
}

/**
 * Cancel all orders for a symbol
 */
export async function cancelAll(symbol: string, exchangeId?: ExchangeId): Promise<CancelResult[] | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called cancelAll with params: %j', { symbol, exchangeId });
        const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
        const results = await exchange.cancelAllOrders(adaptedSymbol);
        logger.info('Cancelled all orders for %s', adaptedSymbol);
        logger.debug('cancelAll result: %j', results);
        return (Array.isArray(results) ? results : [results]).map((result: any) => ({
            orderId: String(result.id),
            symbol: result.symbol,
            status: result.status,
            info: result.info,
        }));
    } catch (error) {
        logger.error('Error cancelling all orders for %s: %s', symbol, error);
        return null;
    }
}

/**
 * Get trade history for a symbol
 */
export async function trades(symbol: string, exchangeId?: ExchangeId): Promise<Trade[] | null> {
    const exchange = getExchange(exchangeId);
    try {
        logger.debug('Called trades with params: %j', { symbol, exchangeId });
        const adaptedSymbol = adaptSymbolForExchange(symbol, exchangeId);
        const trades = await exchange.fetchMyTrades(adaptedSymbol);
        logger.info('Fetched trades for %s', adaptedSymbol);
        logger.debug('trades result: %j', trades);
        return trades.map((t: any) => ({
            id: String(t.id),
            orderId: t.order ? String(t.order) : undefined,
            symbol: t.symbol,
            side: t.side,
            price: Number(t.price),
            amount: Number(t.amount),
            cost: Number(t.cost),
            fee: t.fee ? { cost: Number(t.fee.cost), currency: t.fee.currency } : undefined,
            timestamp: t.timestamp,
            info: t.info,
        }));
    } catch (error) {
        logger.error('Error fetching trades for %s: %s', symbol, error);
        return null;
    }
}

// After initializing all exchanges
logger.info('Supported exchanges: %j', SUPPORTED_EXCHANGES);
logger.info(
    'Configured exchanges: %j',
    availableConfigs.map(c => c.id)
);
