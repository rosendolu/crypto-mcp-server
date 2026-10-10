import * as ccxtProvider from '@/data-providers/ccxt';
import { adaptSymbolForExchange } from '@/data-providers/ccxt';
import { calculateIndicator } from '@/indicators/indicatorService';
import { IndicatorInput } from '@/types/indicators.types';
import logger from '@/utils/logger';
import dayjs from 'dayjs';
import fs from 'fs';
import path from 'path';
import { LOG_DIR } from '@/constant';
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
                const bidRows = result.bids?.slice(0, 10).map(([price, qty]) => [price, qty]) ?? [];
                const askRows = result.asks?.slice(0, 10).map(([price, qty]) => [price, qty]) ?? [];
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
    // The rest of tools remain unchanged below, but with added defensive checks where appropriate
    // ...
}
