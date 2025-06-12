import dotenv from 'dotenv';
import path from 'path';

// Export function to load environment variables
export default function setupEnv() {
    const rootDir = process.cwd();
    dotenv.config({
        path: [
            path.join(rootDir, '.env.local'),
            path.join(rootDir, '.env.development'),
            path.join(rootDir, '.env.production'),
            path.join(rootDir, '.env'),
        ],
        override: false,
    });
}
