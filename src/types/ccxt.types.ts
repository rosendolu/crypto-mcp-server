// Basic type definitions for ccxt dataProvider

// ExchangeId is now a string, validated at runtime against ccxt.exchanges
export type ExchangeId = string; // Validated at runtime

// Runtime array of supported exchanges (populated from ccxt.exchanges)
export const SUPPORTED_EXCHANGES: string[] = [];
// Note: SUPPORTED_EXCHANGES should be set at runtime from ccxt.exchanges

export interface ExchangeConfig {
    id: ExchangeId;
    apiKey: string;
    secret: string;
}

export interface ExchangeInitResult {
    id: ExchangeId;
    name: string;
    ready: boolean;
    error?: string;
}

// ccxt instance type (to be refined later)
export type ExchangeInstance = any; // For initialization only, replace with specific ccxt type later

export interface TickerData {
    symbol: string;
    price: number;
    timestamp: number;
}

export interface BookTicker {
    symbol: string;
    bidPrice: number;
    bidQty: number;
    askPrice: number;
    askQty: number;
    timestamp: number;
}

export interface OrderBook {
    symbol: string;
    bids: [number, number][]; // [price, quantity]
    asks: [number, number][];
    timestamp: number;
}

export interface PrevDayStats {
    symbol: string;
    priceChange: number;
    priceChangePercent: number;
    weightedAvgPrice: number;
    prevClosePrice: number;
    lastPrice: number;
    lastQty: number;
    bidPrice: number;
    askPrice: number;
    openPrice: number;
    highPrice: number;
    lowPrice: number;
    volume: number;
    quoteVolume: number;
    openTime: number;
    closeTime: number;
    firstId?: number;
    lastId?: number;
    count?: number;
}

export interface Candlestick {
    openTime: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
    closeTime: number;
    quoteAssetVolume: number;
    numberOfTrades: number;
    takerBuyBaseAssetVolume: number;
    takerBuyQuoteAssetVolume: number;
    symbol: string;
    interval: string;
}

export interface BalanceAsset {
    asset: string;
    free: number;
    used: number;
    total: number;
}

export interface BalanceInfo {
    assets: BalanceAsset[];
    timestamp: number;
}

export interface DustLog {
    asset: string;
    amount: number;
    serviceChargeAmount: number;
    operateTime: number;
    transferedAmount: number;
    fromAsset: string;
    toAsset: string;
    status: string;
}

export type OrderSide = 'buy' | 'sell';
export type OrderType = 'limit' | 'market' | 'STOP_LOSS' | 'STOP_LOSS_LIMIT' | 'TAKE_PROFIT' | 'TAKE_PROFIT_LIMIT';

export interface OrderResult {
    orderId: string;
    symbol: string;
    status: string;
    type: OrderType;
    side: OrderSide;
    price: number;
    amount: number;
    filled: number;
    timestamp: number;
    info?: any;
}

export interface OrderStatus {
    orderId: string;
    symbol: string;
    status: string;
    type: OrderType;
    side: OrderSide;
    price: number;
    amount: number;
    filled: number;
    remaining: number;
    timestamp: number;
    info?: any;
}

export interface Order {
    orderId: string;
    symbol: string;
    status: string;
    type: OrderType;
    side: OrderSide;
    price: number;
    amount: number;
    filled: number;
    remaining: number;
    timestamp: number;
    info?: any;
}

export interface CancelResult {
    orderId: string;
    symbol: string;
    status: string;
    info?: any;
}

export interface Trade {
    id: string;
    orderId?: string;
    symbol: string;
    side: OrderSide;
    price: number;
    amount: number;
    cost: number;
    fee?: {
        cost: number;
        currency: string;
    };
    timestamp: number;
    info?: any;
}
