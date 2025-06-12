#!/usr/bin/env node

// Import environment setup first
import setupEnv from '@/utils/env';

// Setup environment variables
setupEnv();

// Then import the rest of the application
import { startMcpStdioServer } from '@/api/mcp';
import logger from '@/utils/logger';

logger.info('Starting Crypto MCP CLI...');

// Start the MCP server with stdio transport
startMcpStdioServer().catch(error => {
    logger.error(`Error in MCP server: %s`, error);
    process.exit(1);
});
