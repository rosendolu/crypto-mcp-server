import logger from '@/utils/logger';
import { z } from 'zod';

/**
 * Register all MCP prompts
 */
export function registerPrompts(server: any) {
    // Prompt: Market Analysis
    server.prompt(
        'marketAnalysis',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., BTC/USDT, ETH/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        ({ symbol, exchange }: { symbol: string; exchange?: string }) => {
            logger.debug('Prompt marketAnalysis - Input parameters: %j', { symbol, exchange });

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text: `Please analyze the market situation of ${symbol} according to the technical analysis framework in the @market-analyze.mdc rule.\n\n**Analysis Process:**\n1. Use the "candlesticks" tool to obtain price data for ${symbol}.\n2. Follow the multi-indicator resonance, trend, momentum, volume, and volatility principles as described in the @market-analyze.mdc rule.\n3. Calculate and interpret key indicators (EMA, MACD, RSI, Bollinger Bands, Volume, etc.) from the candlestick data.\n4. Provide a comprehensive analysis and potential trading signals, referencing the step-by-step process and risk control strategies in the @market-analyze.mdc rule.\n\nFor details, see the @market-analyze.mdc rule.`,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Support/Resistance Analysis
    server.prompt(
        'supportResistanceAnalysis',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., BTC/USDT, ETH/USDT'),
            interval: z.string().describe('Candlestick interval, e.g., 4h, 1d'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        ({ symbol, interval, exchange }: { symbol: string; interval: string; exchange?: string }) => {
            logger.debug('Prompt supportResistanceAnalysis - Input parameters: %j', { symbol, interval, exchange });

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text: `Please analyze the support and resistance levels for ${symbol} on the ${interval} timeframe.
1. First use the "candlesticks" tool to get candlestick data
2. Determine major support and resistance areas based on price history
3. Check if price is currently near these levels
4. Consider how indicators like RSI confirm these levels (calculate from candlesticks)
5. Suggest potential trading strategies based on these levels`,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Indicator Analysis
    server.prompt(
        'indicatorAnalysis',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., BTC/USDT, ETH/USDT'),
            interval: z.string().describe('Candlestick interval, e.g., 1h, 4h, 1d'),
            indicator: z.string().describe('Indicator to analyze (e.g., rsi, macd, bb)'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        ({
            symbol,
            interval,
            indicator,
            exchange,
        }: {
            symbol: string;
            interval: string;
            indicator: string;
            exchange?: string;
        }) => {
            logger.debug('Prompt indicatorAnalysis - Input parameters: %j', { symbol, interval, indicator, exchange });

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text: `Please perform a detailed analysis of ${symbol} on the ${interval} timeframe using the ${indicator} indicator.
1. Use the "candlesticks" tool to get price data
2. Calculate the ${indicator} indicator from the candlestick data
3. Interpret the current indicator readings
4. Identify any signals or patterns
5. Place the indicator in the broader market context
6. Suggest potential trading actions based on this analysis`,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Portfolio Analysis
    server.prompt(
        'portfolioAnalysis',
        {
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        ({ exchange }: { exchange?: string }) => {
            logger.debug('Prompt portfolioAnalysis - Input parameters: %j', { exchange });

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text: `Please analyze my current crypto portfolio and provide insights.
1. Use the "balance" tool to retrieve my current holdings
2. Calculate the total portfolio value in USD (using "prices" tool for each asset)
3. Analyze the portfolio allocation and diversification
4. Check the current market status of each holding using "prices" and "prevDay" tools
5. Provide suggestions for rebalancing or optimizing the portfolio based on current market conditions`,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Trading Status
    server.prompt(
        'tradingStatus',
        {
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        ({ exchange }: { exchange?: string }) => {
            logger.debug('Prompt tradingStatus - Input parameters: %j', { exchange });

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text: `Please provide a comprehensive overview of my current trading status.
1. Use the "balance" tool to check my account balance
2. Use the "openOrders" tool to view my pending orders
3. Use the "balance" tool to analyze my current holdings
4. Summarize my overall trading status, including total value, exposure to different assets, and pending orders
5. Provide any relevant recommendations based on current market conditions`,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Multi-Timeframe Analysis
    server.prompt(
        'multiTimeframeAnalysis',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., BTC/USDT, ETH/USDT'),
            exchange: z.string().optional().describe('Exchange id, e.g., binance, okx, gate, etc.'),
        },
        ({ symbol, exchange }: { symbol: string; exchange?: string }) => {
            logger.debug('Prompt multiTimeframeAnalysis - Input parameters: %j', { symbol, exchange });

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text: `Please perform a multi-timeframe analysis for ${symbol} across different timeframes.
1. Analyze the long-term trend using the 1d timeframe with the "candlesticks" tool and relevant indicators
2. Analyze the medium-term trend using the 4h timeframe
3. Analyze the short-term trend using the 1h timeframe
4. Identify confluence between timeframes (where multiple timeframes suggest the same direction)
5. Check for divergence between price action and indicators like RSI or MACD (calculate from candlesticks)
6. Propose a trading strategy that aligns with trends across multiple timeframes`,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Log Analysis and Troubleshooting
    server.prompt(
        'logAnalysis',
        {
            problemType: z
                .enum(['error', 'performance', 'api', 'general'])
                .optional()
                .describe('Type of problem to investigate (error, performance, api, general)'),
            timeRange: z
                .enum(['today', 'yesterday', 'recent'])
                .optional()
                .default('today')
                .describe('Time range to analyze (today, yesterday, recent)'),
            severity: z
                .enum(['critical', 'moderate', 'low'])
                .optional()
                .default('moderate')
                .describe('Analysis severity level (critical, moderate, low)'),
        },
        ({
            problemType,
            timeRange,
            severity,
        }: {
            problemType?: 'error' | 'performance' | 'api' | 'general';
            timeRange?: 'today' | 'yesterday' | 'recent';
            severity?: 'critical' | 'moderate' | 'low';
        }) => {
            logger.debug('Prompt logAnalysis - Input parameters: %j', { problemType, timeRange, severity });

            const severityConfig = {
                critical: {
                    levels: ['emerg', 'alert', 'crit', 'error'],
                    focus: 'critical issues and system failures',
                    urgency: 'immediate attention required',
                },
                moderate: {
                    levels: ['error', 'warning', 'notice'],
                    focus: 'errors and important warnings',
                    urgency: 'should be addressed soon',
                },
                low: {
                    levels: ['info', 'debug'],
                    focus: 'general information and debugging',
                    urgency: 'informational review',
                },
            };

            const config = severityConfig[severity || 'moderate'];
            const problemContext = problemType ? ` focusing on ${problemType} related issues` : '';

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text: `Please analyze the system logs to help troubleshoot issues${problemContext}. 

**Analysis Configuration:**
- Time Range: ${timeRange}
- Severity: ${severity} (${config.urgency})
- Focus: ${config.focus}
- Log Levels: ${config.levels.join(', ')}

**Step-by-Step Analysis Process:**

1. **Initial Log Overview**
   - Use "analyzeLogs" tool with date="${timeRange}" to get overall log summary
   - Identify the total number of log entries and any immediate patterns

2. **Error Analysis** (if severity is critical or moderate)
   - Use "analyzeLogs" with search="error" to find all error messages
   - Use "analyzeLogs" with search="warning" for warning analysis
   - Look for recurring error patterns and their frequency

3. **Problem-Specific Investigation**
   ${
       problemType === 'api'
           ? `\n   - Search for API-related issues using search="API" or search="HTTP"\n   - Look for connection timeouts, rate limits, or authentication failures\n   - Check for exchange-related errors if trading issues occur`
           : ''
   }
   ${
       problemType === 'performance'
           ? `\n   - Search for performance keywords using search="timeout" or search="slow"\n   - Look for memory or CPU related messages\n   - Check for database or network latency issues`
           : ''
   }
   ${
       problemType === 'error'
           ? `\n   - Focus on error and critical level logs\n   - Use search functionality to find specific error messages\n   - Trace error sequences and their root causes`
           : ''
   }`,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Create Order
    server.prompt(
        'createOrderPrompt',
        {
            symbol: z.string().describe('Trading pair symbol, e.g., BTC/USDT, ETH/USDT'),
            side: z.enum(['BUY', 'SELL']).describe('Order side: BUY or SELL'),
            quantity: z.string().describe('Order quantity (in base asset)'),
            type: z
                .enum(['MARKET', 'LIMIT'])
                .optional()
                .default('MARKET')
                .describe('Order type: MARKET (default) or LIMIT'),
            price: z.string().optional().describe('Limit price (required for LIMIT orders)'),
        },
        ({
            symbol,
            side,
            quantity,
            type,
            price,
        }: {
            symbol: string;
            side: 'BUY' | 'SELL';
            quantity: string;
            type?: 'MARKET' | 'LIMIT';
            price?: string;
        }) => {
            logger.debug('Prompt createOrderPrompt - Input parameters: %j', { symbol, side, quantity, type, price });

            let text = `I want to place an order for ${symbol} (${side}) with quantity ${quantity}`;
            if (type === 'LIMIT') {
                text += ` as a LIMIT order`;
                text += price
                    ? ` at price ${price}.`
                    : '. Please fetch the latest price using the "prices" tool and suggest a reasonable limit price.';
            } else {
                text += ' as a MARKET order.';
            }
            text += `\n\nPlease use the "createOrder" tool. Required parameters:\n- symbol: ${symbol}\n- side: ${side}\n- type: ${
                type || 'MARKET'
            }\n- quantity: ${quantity}`;
            if (type === 'LIMIT') {
                text += '\n- price: (user specified or suggested)';
            }
            text += '\nIf the user did not specify a price for LIMIT, suggest one based on the latest price.';

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Cancel Order
    server.prompt(
        'cancelOrderPrompt',
        {
            symbol: z
                .string()
                .optional()
                .describe(
                    'Trading pair symbol, e.g., BTC/USDT, ETH/USDT (optional, leave empty to list all open orders)'
                ),
        },
        ({ symbol }: { symbol?: string }) => {
            logger.debug('Prompt cancelOrderPrompt - Input parameters: %j', { symbol });

            let text = `I want to cancel an order.`;
            text += '\n\nFirst, use the "openOrders" tool';
            if (symbol) {
                text += ` for symbol ${symbol}`;
            }
            text += ' to list all open orders.';
            text += '\n\nThen, ask the user to specify which order to cancel (orderId or origClientOrderId).';
            text += '\n\nTo cancel, use the "cancelOrder" tool with parameters:';
            text += '\n- symbol: (required)';
            text += '\n- orderId: (optional, if user specifies)';
            text += '\n- origClientOrderId: (optional, if user specifies)';
            text += '\n\nIf the user does not know the orderId, help them find it from the open orders list.';

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Get Open Orders
    server.prompt(
        'getOpenOrdersPrompt',
        {
            symbol: z
                .string()
                .optional()
                .describe('Trading pair symbol, e.g., BTC/USDT, ETH/USDT (optional, leave empty to get all)'),
        },
        ({ symbol }: { symbol?: string }) => {
            logger.debug('Prompt getOpenOrdersPrompt - Input parameters: %j', { symbol });

            let text = `Please list all my open orders`;
            if (symbol) {
                text += ` for symbol ${symbol}`;
            }
            text += '.\n\nUse the "openOrders" tool to fetch the open orders.';
            text += '\n\nDisplay the orderId, origClientOrderId, price, quantity, and order type for each open order.';

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text,
                        },
                    },
                ],
            };
        }
    );

    // Prompt: Query Account Balance
    server.prompt(
        'queryAccountBalancePrompt',
        {
            provider: z
                .enum(['binance', 'gate'])
                .optional()
                .describe('Which data provider to query: binance, gate, or leave empty for all'),
        },
        ({ provider }: { provider?: 'binance' | 'gate' }) => {
            logger.debug('Prompt queryAccountBalancePrompt - Input parameters: %j', { provider });

            let text = 'I want to check my account balance';
            if (provider) {
                text += ` on ${provider}`;
            } else {
                text += ' on all supported data providers (binance, gate, etc.)';
            }
            text += '.\n\nPlease use the "balance" tool for each provider.';
            text += '\n- If provider is not specified, query all supported providers.';
            text += '\n- For each provider, filter out tokens where free + locked = 0.';
            text += '\n- Present the result in a table format with columns: asset, free, locked, total.';
            text += '\n- If querying multiple providers, group the tables by provider.';
            text +=
                '\n- The table should clearly show the asset, free amount, locked amount, and total amount for each token.';

            return {
                messages: [
                    {
                        role: 'user',
                        content: {
                            type: 'text',
                            text,
                        },
                    },
                ],
            };
        }
    );
}
