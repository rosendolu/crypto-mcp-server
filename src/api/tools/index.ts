import * as ccxtProvider from '@/data-providers/ccxt';
import { adaptSymbolForExchange } from '@/data-providers/ccxt';
import { calculateIndicator } from '@/indicators/indicatorService';
import { IndicatorInput } from '@/types/indicators.types';
import logger from '@/utils/logger';
import dayjs from 'dayjs';
import fs from 'fs';
import path from 'path';
import { z } from 'zod';

function toMarkdownTable(headers: string[], rows: (string | number)[][]): string {
    const headerLine = `| ${headers.join(' | ')} |`;
    const separator = `|${headers.map(() => '---').join('|')}|`;
    const rowLines = rows.map(row => `| ${row.join(' | ')} |`).join('\n');
    return `${headerLine}\n${separator}\n${rowLines}`;
}

export function registerTools(server: any) {
    // Market Data
    server.tool(
        'prices',
        {
            symbol: z.string().optional().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, exchange }: { symbol?: string; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool prices called with params: %j', { symbol, exchange });
            try {
                const result = await ccxtProvider.prices(symbol, exchange);
                logger.debug('Tool prices result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in prices tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'bookTickers',
        {
            symbol: z.string().optional().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, exchange }: { symbol?: string; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool bookTickers called with params: %j', { symbol, exchange });
            try {
                const result = await ccxtProvider.bookTickers(symbol, exchange);
                if (!result) return { content: [{ type: 'text', text: 'No data.' }], isError: true };
                const arr = Array.isArray(result) ? result : [result];
                const headers = ['Symbol', 'Bid Price', 'Bid Qty', 'Ask Price', 'Ask Qty', 'Timestamp'];
                const rows = arr.map(r => [r.symbol, r.bidPrice, r.bidQty, r.askPrice, r.askQty, r.timestamp]);
                logger.debug('Tool bookTickers result: %j', result);
                return { content: [{ type: 'text', text: toMarkdownTable(headers, rows) }] };
            } catch (error) {
                logger.error('Error in bookTickers tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'depth',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, exchange }: { symbol: string; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool depth called with params: %j', { symbol, exchange });
            try {
                const result = await ccxtProvider.depth(symbol, exchange);
                if (!result) return { content: [{ type: 'text', text: 'No data.' }], isError: true };
                const bidRows = result.bids.slice(0, 10).map(([price, qty]) => [price, qty]);
                const askRows = result.asks.slice(0, 10).map(([price, qty]) => [price, qty]);
                const bidTable = toMarkdownTable(['Bid Price', 'Bid Qty'], bidRows);
                const askTable = toMarkdownTable(['Ask Price', 'Ask Qty'], askRows);
                logger.debug('Tool depth result: %j', result);
                return {
                    content: [{ type: 'text', text: `**Bids**\n${bidTable}\n\n**Asks**\n${askTable}` }],
                };
            } catch (error) {
                logger.error('Error in depth tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'prevDay',
        {
            symbol: z
                .union([z.string(), z.boolean()])
                .optional()
                .describe('Trading pair symbol (e.g., ETH/USDT) or false for all'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, exchange }: { symbol?: string | false; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool prevDay called with params: %j', { symbol, exchange });
            try {
                const result = await ccxtProvider.prevDay(symbol, exchange);
                logger.debug('Tool prevDay result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in prevDay tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );

    // Account Information
    server.tool(
        'balance',
        {
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ exchange }: { exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool balance called with params: %j', { exchange });
            try {
                const result = await ccxtProvider.balance(exchange);
                if (!result) return { content: [{ type: 'text', text: 'No data.' }], isError: true };
                const headers = ['Asset', 'Free', 'Used', 'Total'];
                const rows = result.assets.map(a => [a.asset, a.free, a.used, a.total]);
                logger.debug('Tool balance result: %j', result);
                return { content: [{ type: 'text', text: toMarkdownTable(headers, rows) }] };
            } catch (error) {
                logger.error('Error in balance tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'dustLog',
        {
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ exchange }: { exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool dustLog called with params: %j', { exchange });
            try {
                const result = await ccxtProvider.dustLog(exchange);
                logger.debug('Tool dustLog result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in dustLog tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );

    // Order Operations
    server.tool(
        'buy',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            quantity: z.number(),
            price: z.number(),
            options: z.object({ type: z.string().optional(), icebergQty: z.number().optional() }).optional(),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({
            symbol,
            quantity,
            price,
            options,
            exchange,
        }: {
            symbol: string;
            quantity: number;
            price: number;
            options?: any;
            exchange?: string;
        }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool buy called with params: %j', { symbol, quantity, price, options, exchange });
            try {
                const result = await ccxtProvider.buy(symbol, quantity, price, options, exchange);
                logger.debug('Tool buy result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in buy tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'sell',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            quantity: z.number(),
            price: z.number(),
            options: z.object({ type: z.string().optional(), icebergQty: z.number().optional() }).optional(),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({
            symbol,
            quantity,
            price,
            options,
            exchange,
        }: {
            symbol: string;
            quantity: number;
            price: number;
            options?: any;
            exchange?: string;
        }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool sell called with params: %j', {
                symbol,
                quantity,
                price,
                options,
                exchange,
            });
            try {
                const result = await ccxtProvider.sell(symbol, quantity, price, options, exchange);
                logger.debug('Tool sell result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in sell tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'marketBuy',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            quantity: z.number(),
            options: z.object({}).optional(),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({
            symbol,
            quantity,
            options,
            exchange,
        }: {
            symbol: string;
            quantity: number;
            options?: any;
            exchange?: string;
        }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool marketBuy called with params: %j', { symbol, quantity, options, exchange });
            try {
                const result = await ccxtProvider.marketBuy(symbol, quantity, options, exchange);
                logger.debug('Tool marketBuy result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in marketBuy tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'marketSell',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            quantity: z.number(),
            options: z.object({}).optional(),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({
            symbol,
            quantity,
            options,
            exchange,
        }: {
            symbol: string;
            quantity: number;
            options?: any;
            exchange?: string;
        }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool marketSell called with params: %j', { symbol, quantity, options, exchange });
            try {
                const result = await ccxtProvider.marketSell(symbol, quantity, options, exchange);
                logger.debug('Tool marketSell result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in marketSell tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'orderStatus',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            orderId: z.string(),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, orderId, exchange }: { symbol: string; orderId: string; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool orderStatus called with params: %j', { symbol, orderId, exchange });
            try {
                const result = await ccxtProvider.orderStatus(symbol, orderId, exchange);
                if (!result) return { content: [{ type: 'text', text: 'No data.' }], isError: true };
                const headers = [
                    'Order ID',
                    'Symbol',
                    'Status',
                    'Type',
                    'Side',
                    'Price',
                    'Amount',
                    'Filled',
                    'Remaining',
                    'Timestamp',
                ];
                const rows = [
                    [
                        result.orderId,
                        result.symbol,
                        result.status,
                        result.type,
                        result.side,
                        result.price,
                        result.amount,
                        result.filled,
                        result.remaining,
                        result.timestamp,
                    ],
                ];
                logger.debug('Tool orderStatus result: %j', result);
                return { content: [{ type: 'text', text: toMarkdownTable(headers, rows) }] };
            } catch (error) {
                logger.error('Error in orderStatus tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'allOrders',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, exchange }: { symbol: string; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool allOrders called with params: %j', { symbol, exchange });
            try {
                const result = await ccxtProvider.allOrders(symbol, exchange);
                if (!result) return { content: [{ type: 'text', text: 'No data.' }], isError: true };
                const headers = [
                    'Order ID',
                    'Symbol',
                    'Status',
                    'Type',
                    'Side',
                    'Price',
                    'Amount',
                    'Filled',
                    'Remaining',
                    'Timestamp',
                ];
                const rows = result.map(o => [
                    o.orderId,
                    o.symbol,
                    o.status,
                    o.type,
                    o.side,
                    o.price,
                    o.amount,
                    o.filled,
                    o.remaining,
                    o.timestamp,
                ]);
                logger.debug('Tool allOrders result: %j', result);
                return { content: [{ type: 'text', text: toMarkdownTable(headers, rows) }] };
            } catch (error) {
                logger.error('Error in allOrders tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );

    server.tool(
        'openOrders',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, exchange }: { symbol: string; exchange?: string }) => {
            const adaptedSymbol = adaptSymbolForExchange(symbol, exchange);
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool openOrders called with params: %j', { symbol, exchange });
            try {
                const result = await ccxtProvider.openOrders(adaptedSymbol, exchange);
                if (!result) return { content: [{ type: 'text', text: 'No data.' }], isError: true };
                const headers = [
                    'Order ID',
                    'Symbol',
                    'Status',
                    'Type',
                    'Side',
                    'Price',
                    'Amount',
                    'Filled',
                    'Remaining',
                    'Timestamp',
                ];
                const rows = result.map(o => [
                    o.orderId,
                    o.symbol,
                    o.status,
                    o.type,
                    o.side,
                    o.price,
                    o.amount,
                    o.filled,
                    o.remaining,
                    o.timestamp,
                ]);
                logger.debug('Tool openOrders result: %j', result);
                return { content: [{ type: 'text', text: toMarkdownTable(headers, rows) }] };
            } catch (error) {
                logger.error('Error in openOrders tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'cancel',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            orderId: z.string(),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, orderId, exchange }: { symbol: string; orderId: string; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool cancel called with params: %j', { symbol, orderId, exchange });
            try {
                const result = await ccxtProvider.cancel(symbol, orderId, exchange);
                logger.debug('Tool cancel result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in cancel tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'cancelAll',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, exchange }: { symbol: string; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool cancelAll called with params: %j', { symbol, exchange });
            try {
                const result = await ccxtProvider.cancelAll(symbol, exchange);
                logger.debug('Tool cancelAll result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in cancelAll tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
    server.tool(
        'trades',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({ symbol, exchange }: { symbol: string; exchange?: string }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool trades called with params: %j', { symbol, exchange });
            try {
                const result = await ccxtProvider.trades(symbol, exchange);
                if (!result) return { content: [{ type: 'text', text: 'No data.' }], isError: true };
                const headers = [
                    'Trade ID',
                    'Order ID',
                    'Symbol',
                    'Side',
                    'Price',
                    'Amount',
                    'Cost',
                    'Fee',
                    'Timestamp',
                ];
                const rows = result.map(t => [
                    t.id,
                    t.orderId || '',
                    t.symbol,
                    t.side,
                    t.price,
                    t.amount,
                    t.cost,
                    t.fee ? `${t.fee.cost} ${t.fee.currency}` : '',
                    t.timestamp,
                ]);
                logger.debug('Tool trades result: %j', result);
                return { content: [{ type: 'text', text: toMarkdownTable(headers, rows) }] };
            } catch (error) {
                logger.error('Error in trades tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );

    // Tool: Check all supported exchanges for API key/secret config
    server.tool('checkExchangeConfigs', {}, async () => {
        try {
            const results = ccxtProvider.checkExchangeConfigs();
            const headers = ['Exchange ID', 'Name', 'Ready', 'Error'];
            const rows = results.map(r => [r.id, r.name, r.ready ? '✅' : '❌', r.error || '']);
            logger.debug('Tool checkExchangeConfigs result: %j', results);
            return { content: [{ type: 'text', text: toMarkdownTable(headers, rows) }] };
        } catch (error) {
            logger.error('Error in checkExchangeConfigs tool: %s', error);
            return { content: [{ type: 'text', text: String(error) }], isError: true };
        }
    });

    // Log analysis tool (basic)
    server.tool(
        'analyzeLogs',
        {
            date: z.string().describe('Log date: YYYY-MM-DD, "today", or "yesterday"'),
        },
        async ({ date }: { date: string }) => {
            try {
                logger.debug('Tool analyzeLogs called with params: %j', { date });
                const LOG_DIR = require('@/constant').LOG_DIR;
                if (!fs.existsSync(LOG_DIR)) {
                    return {
                        content: [{ type: 'text', text: `Log directory not found: ${LOG_DIR}` }],
                        isError: true,
                    };
                }
                let targetDate: string;
                const today = dayjs();
                if (!date || date === 'today') {
                    targetDate = today.format('YYYY-MM-DD');
                } else if (date === 'yesterday') {
                    targetDate = today.subtract(1, 'day').format('YYYY-MM-DD');
                } else {
                    targetDate = date;
                }
                // Find the log file for the date (assume only one file per date, or pick the first if multiple)
                const files = fs.readdirSync(LOG_DIR);
                const logFile = files.find((f: string) => f.startsWith(targetDate));
                if (!logFile) {
                    return {
                        content: [{ type: 'text', text: `No log file found for date: ${targetDate}` }],
                        isError: true,
                    };
                }
                const filePath = path.join(LOG_DIR, logFile);
                const fileContent = fs.readFileSync(filePath, 'utf-8');
                return {
                    content: [{ type: 'text', text: fileContent }],
                    isError: false,
                };
            } catch (err: any) {
                logger.error('analyzeLogs error: %s', err.message);
                return {
                    content: [{ type: 'text', text: `Error reading log file: ${err.message}` }],
                    isError: true,
                };
            }
        }
    );
    server.tool(
        'candlesticks',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            interval: z.string().describe('Candlestick interval, e.g., 1m, 5m, 1h, 1d'),
            options: z.record(z.any()).optional().describe('Additional options for fetchOHLCV'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        async ({
            symbol,
            interval,
            options,
            exchange,
        }: {
            symbol: string;
            interval: string;
            options?: object;
            exchange?: string;
        }) => {
            if (!exchange) logger.warn('No exchange specified, defaulting to binance.');
            logger.debug('Tool candlesticks called with params: %j', {
                symbol,
                interval,
                options,
                exchange,
            });
            try {
                const result = await ccxtProvider.candlesticks(symbol, interval, options, exchange);
                if (!result) {
                    logger.error('No candlestick data returned for %s %s on %s', symbol, interval, exchange);
                    return { content: [{ type: 'text', text: 'No candlestick data available.' }], isError: true };
                }
                // logger.debug('Tool candlesticks result: %j', result);
                return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
            } catch (error) {
                logger.error('Error in candlesticks tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );

    server.tool(
        'calculateIndicators',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., ETH/USDT, BTC/USDT'),
            interval: z.string().describe('Candlestick interval, e.g., 1m, 5m, 1h, 1d'),
            options: z.record(z.any()).optional().describe('Additional options for fetchOHLCV'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
            indicators: z
                .array(z.string())
                .default(['macd', 'rsi', 'bollinger bands', 'kdj', 'ema', 'atr', 'cmf'])
                .describe(
                    'Indicators to calculate, supported: ["macd", "rsi", "bollinger bands", "kdj", "ema", "atr"]'
                ),
            period: z.number().optional().default(14).describe('Default period for indicators'),
            fastPeriod: z.number().optional().default(12).describe('Fast period for MACD'),
            slowPeriod: z.number().optional().default(26).describe('Slow period for MACD'),
            signalPeriod: z.number().optional().default(9).describe('Signal period for MACD and Stochastic'),
            stdDev: z.number().optional().default(2).describe('Standard deviation for Bollinger Bands'),
        },
        async ({
            symbol,
            interval,
            options,
            exchange,
            indicators,
            period = 14,
            fastPeriod = 12,
            slowPeriod = 26,
            signalPeriod = 9,
            stdDev = 2,
        }: {
            symbol: string;
            interval: string;
            options?: object;
            exchange?: string;
            indicators: string[];
            period?: number;
            fastPeriod?: number;
            slowPeriod?: number;
            signalPeriod?: number;
            stdDev?: number;
        }) => {
            const candlesticks = await ccxtProvider.candlesticks(symbol, interval, options, exchange);
            if (!candlesticks) {
                logger.error('No candlestick data returned for %s %s on %s', symbol, interval, exchange);
                return { content: [{ type: 'text', text: 'No candlestick data available.' }], isError: true };
            }
            logger.debug('Tool calculateIndicators called with params: %j', {
                candlesticksCount: candlesticks.length,
                symbol,
                interval,
                exchange,
                indicators,
                period,
                fastPeriod,
                slowPeriod,
                signalPeriod,
                stdDev,
            });

            const input: IndicatorInput = {
                values: candlesticks.map((c: any) => c.close),
                high: candlesticks.map((c: any) => c.high),
                low: candlesticks.map((c: any) => c.low),
                close: candlesticks.map((c: any) => c.close),
                volume: candlesticks.map((c: any) => c.volume),
                open: candlesticks.map((c: any) => c.open),
                period,
                fastPeriod,
                slowPeriod,
                signalPeriod,
                stdDev,
            };

            try {
                const result: { [key: string]: any } = {};

                for (const indicator of indicators) {
                    try {
                        result[indicator] = calculateIndicator(indicator, input);
                    } catch (error) {
                        logger.error('Error calculating indicator %s: %s', indicator, error);
                        result[indicator] = null;
                    }
                }

                return {
                    content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
                };
            } catch (error) {
                logger.error('Error in calculateIndicators tool: %s', error);
                return { content: [{ type: 'text', text: String(error) }], isError: true };
            }
        }
    );
}
