import { LOG_DIR } from '@/constant';
import fs from 'fs';
import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';

const logDir = LOG_DIR;
if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
}

const dailyRotateFileTransport = new DailyRotateFile({
    dirname: logDir,
    filename: '%DATE%.log',
    datePattern: 'YYYY-MM-DD',
    maxFiles: '7d',
    zippedArchive: false,
});

const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
        winston.format.timestamp({
            format: 'YYYY-MM-DD HH:mm:ss',
        }),
        winston.format.splat(),
        winston.format.printf(({ timestamp, level, message, ...meta }) => {
            const metaString = Object.keys(meta).length ? JSON.stringify(meta) : '';
            return `${timestamp} [${level}]: ${message} ${metaString}`.trim();
        })
    ),
    transports: [dailyRotateFileTransport, new winston.transports.Console()],
});

export default logger;
