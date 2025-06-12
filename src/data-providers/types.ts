export interface KlineParams {
    /** Symbol must be in BASE/QUOTE format, e.g., BTC/USDT */
    symbol: string;
    interval: string; // e.g., '1m', '5m', '1h', etc.
    limit?: number; // number of data points
    startTime?: number;
    endTime?: number;
}

export interface KlineData {
    openTime: number;
    open: string;
    high: string;
    low: string;
    close: string;
    volume: string;
    closeTime: number;
    quoteAssetVolume: string;
    numberOfTrades: number;
    takerBuyBaseAssetVolume: string;
    takerBuyQuoteAssetVolume: string;
}

export interface TradeParams {
    /** Symbol must be in BASE/QUOTE format, e.g., BTC/USDT */
    symbol: string;
    limit?: number;
}

export interface TradeData {
    id: number | string;
    price: string;
    qty: string;
    time: number;
    isBuyerMaker: boolean;
    isBestMatch: boolean;
    [key: string]: any;
}

export interface OrderBookParams {
    /** Symbol must be in BASE/QUOTE format, e.g., BTC/USDT */
    symbol: string;
    limit?: number;
}

export interface OrderBookData {
    lastUpdateId: number;
    bids: [string, string][]; // [price, quantity]
    asks: [string, string][]; // [price, quantity]
}

export interface OrderParams {
    /** Symbol must be in BASE/QUOTE format, e.g., BTC/USDT */
    symbol?: string;
    orderId?: number;
    origClientOrderId?: string;
}

export interface OrderData {
    symbol: string;
    orderId: number;
    orderListId: number;
    clientOrderId: string;
    price: string;
    origQty: string;
    executedQty: string;
    cummulativeQuoteQty: string;
    status: string;
    timeInForce: string;
    type: string;
    side: string;
    stopPrice?: string;
    icebergQty?: string;
    time: number;
    updateTime: number;
    isWorking: boolean;
    origQuoteOrderQty: string;
    [key: string]: any;
}

export interface AccountData {
    makerCommission: number;
    takerCommission: number;
    buyerCommission: number;
    sellerCommission: number;
    canTrade: boolean;
    canWithdraw: boolean;
    canDeposit: boolean;
    updateTime: number;
    accountType: string;
    balances: BalanceData[];
    permissions: string[];
    [key: string]: any;
}

export interface BalanceData {
    asset: string;
    free: string;
    locked: string;
    [key: string]: any;
}

export interface PositionData {
    /** Symbol must be in BASE/QUOTE format, e.g., BTC/USDT */
    symbol: string;
    positionAmt: string;
    entryPrice: string;
    markPrice: string;
    unRealizedProfit: string;
    liquidationPrice: string;
    leverage: string;
    marginType: string;
    [key: string]: any;
}

export interface MarketData {
    /** Symbol must be in BASE/QUOTE format, e.g., BTC/USDT */
    symbol: string;
    price?: string;
    bidPrice?: string;
    bidQty?: string;
    askPrice?: string;
    askQty?: string;
    [key: string]: any;
}

export interface CryptoDataProvider {
    // WebSocket subscriptions
    subscribeKlines(params: KlineParams, onData: (kline: KlineData) => void): () => void;
    subscribeTrades(params: TradeParams, onData: (trade: TradeData) => void): () => void;
    subscribeUserData(onOrder: (order: OrderData) => void, onAccount: (account: AccountData) => void): () => void;
    subscribeMarket(params: { symbol: string }, onData: (market: MarketData) => void): () => void;

    // REST fallback for historical or snapshot data
    getKlines(params: KlineParams): Promise<KlineData[]>;

    // Optional methods that might be implemented by specific providers
    wsTradesRecent?(params: any): Promise<any>;
    wsDepth?(params: any): Promise<any>;
    wsTickerPrice?(params?: any): Promise<any>;
    wsTicker24hr?(params?: any): Promise<any>;
    wsAllOrders?(params?: any): Promise<any>;
    wsAccountBalance?(): Promise<any>;

    // --- Trade API ---
    createOrder?(params: any): Promise<any>;
    testOrder?(params: any): Promise<any>;
    cancelOrder?(params: any): Promise<any>;
    cancelAllOrders?(params: any): Promise<any>;
    createOCOOrder?(params: any): Promise<any>;
    cancelOCOOrder?(params: any): Promise<any>;
    cancelReplaceOrder?(params: any): Promise<any>;
    wsPlaceOrder?(params: any): Promise<any>;
    wsTestOrder?(params: any): Promise<any>;
    wsCancelOrder?(params: any): Promise<any>;
    wsCancelReplaceOrder?(params: any): Promise<any>;
    wsCancelAllOrders?(params: any): Promise<any>;
}

export interface IndicatorParams {
    /** Symbol must be in BASE/QUOTE format, e.g., BTC/USDT */
    symbol: string;
    interval: string;
    indicator: string;
    period?: number;
    fastPeriod?: number;
    slowPeriod?: number;
    signalPeriod?: number;
    stdDev?: number;
}

export interface IndicatorResult {
    /** Symbol must be in BASE/QUOTE format, e.g., BTC/USDT */
    symbol: string;
    interval: string;
    indicator: string;
    params: {
        period: number;
        fastPeriod?: number;
        slowPeriod?: number;
        signalPeriod?: number;
        stdDev?: number;
    };
    timestamp: number;
    klineTimestamps: number[];
    result: any;
}
