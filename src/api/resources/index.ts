import * as ccxtProvider from '@/data-providers/ccxt';
import logger from '@/utils/logger';
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js';
import fs from 'fs';
import path from 'path';

/**
 * Register all MCP resources (ccxt-based, minimal)
 */
export function registerResources(server: any) {
    // Resource: Supported exchanges info
    server.resource(
        'supportedExchanges',
        new ResourceTemplate('supportedExchanges://', { list: undefined }),
        async (uri: any) => {
            try {
                logger.debug('Resource supportedExchanges - Input parameters: %j', {});
                const exchanges = ccxtProvider.getAvailableExchanges();
                return {
                    contents: [
                        {
                            uri: uri.href,
                            text: JSON.stringify(exchanges, null, 2),
                        },
                    ],
                };
            } catch (error) {
                logger.error(`Error fetching supported exchanges: ${error}`);
                throw error;
            }
        }
    );

    // Resource: Project introduction (from README)
    server.resource('projectIntro', new ResourceTemplate('projectIntro://', { list: undefined }), async (uri: any) => {
        try {
            logger.debug('Resource projectIntro - Input parameters: %j', {});
            const readmePath = path.resolve(__dirname, '../../../README.md');
            const readmeContent = fs.readFileSync(readmePath, 'utf-8');
            return {
                contents: [
                    {
                        uri: uri.href,
                        text: readmeContent,
                    },
                ],
            };
        } catch (error) {
            logger.error(`Error fetching project introduction: ${error}`);
            throw error;
        }
    });
}
