import os from 'os';
import path from 'path';

export const LOG_DIR = path.join(os.homedir(), '.crypto-mcp-server', 'logs');
export const devMode = process.env.LOG_LEVEL === 'debug';
