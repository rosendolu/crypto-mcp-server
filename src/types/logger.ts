/**
 * Logger level definitions following syslog standard
 */

export const LOG_LEVELS = {
    emerg: 0,
    alert: 1,
    crit: 2,
    error: 3,
    warning: 4,
    notice: 5,
    info: 6,
    debug: 7,
} as const;

export type LogLevel = keyof typeof LOG_LEVELS;

export const LOG_LEVEL_NAMES: LogLevel[] = ['emerg', 'alert', 'crit', 'error', 'warning', 'notice', 'info', 'debug'];

/**
 * Log level descriptions
 */
export const LOG_LEVEL_DESCRIPTIONS = {
    emerg: 'Emergency - System is unusable',
    alert: 'Alert - Action must be taken immediately',
    crit: 'Critical - Critical conditions',
    error: 'Error - Error conditions',
    warning: 'Warning - Warning conditions',
    notice: 'Notice - Normal but significant condition',
    info: 'Informational - Informational messages',
    debug: 'Debug - Debug-level messages',
} as const;
