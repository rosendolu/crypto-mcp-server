// import { Resource, Tool } from '@modelcontextprotocol/sdk';
import { registerPrompts } from '@/api/prompts';
import { registerResources } from '@/api/resources';
import { registerTools } from '@/api/tools';
import logger from '@/utils/logger';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

/**
 * Create MCP server instance
 */
export function createMcpServer() {
    logger.info('Creating MCP server...');

    const server = new McpServer({
        name: 'Crypto MCP Server',
        version: '1.0.0',
    });

    // Register resources, tools, and prompts
    logger.info('Registering resources...');
    registerResources(server);

    logger.info('Registering tools...');
    registerTools(server);

    logger.info('Registering prompts...');
    registerPrompts(server);

    logger.info('MCP server created successfully');

    return server;
}

/**
 * Start the MCP server with stdio transport
 */
export async function startMcpStdioServer() {
    logger.info('Starting Crypto MCP Stdio Server...');

    const server = createMcpServer();
    const transport = new StdioServerTransport();

    try {
        await server.connect(transport);
        logger.info('Crypto MCP Stdio Server started successfully');
    } catch (error) {
        logger.error(`Error starting MCP server: %s`, error);
        process.exit(1);
    }
}
