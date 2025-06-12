/**
 * Environment variables configuration interface
 */
export interface EnvConfig {
    BINANCE_API_KEY?: string;
    BINANCE_API_SECRET?: string;
}

/**
 * Configuration validation result interface
 */
export interface ConfigValidationResult {
    isValid: boolean;
    warnings: string[];
    errors: string[];
    hasApiCredentials: boolean;
    summary: string;
}

/**
 * Check and validate environment variables
 */
export function validateEnvironmentConfig(): ConfigValidationResult {
    const config: EnvConfig = {
        BINANCE_API_KEY: process.env.BINANCE_API_KEY,
        BINANCE_API_SECRET: process.env.BINANCE_API_SECRET,
    };

    const warnings: string[] = [];
    const errors: string[] = [];

    // Check if API credentials are configured
    const hasApiKey = !!(config.BINANCE_API_KEY && config.BINANCE_API_KEY.trim());
    const hasApiSecret = !!(config.BINANCE_API_SECRET && config.BINANCE_API_SECRET.trim());
    const hasApiCredentials = hasApiKey && hasApiSecret;

    if (!hasApiCredentials) {
        warnings.push('🔑 Binance API credentials are not configured');
        warnings.push('📝 Some features requiring authentication will not work:');
        warnings.push('   • Account balance queries');
        warnings.push('   • Open orders retrieval');
        warnings.push('   • Holdings information');
        warnings.push('   • Position data (for futures)');
        warnings.push('');
        warnings.push('💡 To configure API credentials:');
        warnings.push('   1. Create a .env file in the project root');
        warnings.push('   2. Add the following lines:');
        warnings.push('      BINANCE_API_KEY=your_api_key_here');
        warnings.push('      BINANCE_API_SECRET=your_api_secret_here');
        warnings.push('   3. Restart the MCP server');
        warnings.push('');
        warnings.push('🔒 Note: API keys are only required for account-specific operations.');
        warnings.push('    Market data queries (prices, klines, indicators) work without API keys.');
    }

    // Generate summary
    let summary: string;
    if (errors.length > 0) {
        summary = '❌ Configuration has errors that prevent proper operation';
    } else if (warnings.length > 0) {
        summary = hasApiCredentials
            ? '⚠️  Configuration has minor warnings but API credentials are configured'
            : '⚠️  Limited functionality - API credentials not configured';
    } else {
        summary = '✅ All environment variables are properly configured';
    }

    return {
        isValid: errors.length === 0,
        warnings,
        errors,
        hasApiCredentials,
        summary,
    };
}

/**
 * Get configuration status report for display
 */
export function getConfigurationReport(): string {
    const validation = validateEnvironmentConfig();
    const lines: string[] = [];

    lines.push('🔧 Crypto MCP Server Configuration Status');
    lines.push('='.repeat(50));
    lines.push('');
    lines.push(`📊 Overall Status: ${validation.summary}`);
    lines.push('');

    // API Credentials Status
    lines.push('🔑 API Credentials:');
    if (validation.hasApiCredentials) {
        lines.push('   ✅ Binance API Key: Configured');
        lines.push('   ✅ Binance API Secret: Configured');
        lines.push('   🔓 Account-specific operations: Available');
    } else {
        lines.push('   ❌ Binance API Key: Not configured');
        lines.push('   ❌ Binance API Secret: Not configured');
        lines.push('   🔒 Account-specific operations: Unavailable');
    }
    lines.push('');

    // Available Features
    lines.push('🚀 Available Features:');
    lines.push('   ✅ Market data queries (prices, klines)');
    lines.push('   ✅ Technical indicators');
    lines.push('   ✅ Order book data');
    lines.push('   ✅ Recent trades');

    if (validation.hasApiCredentials) {
        lines.push('   ✅ Account balance');
        lines.push('   ✅ Holdings information');
        lines.push('   ✅ Open orders');
        lines.push('   ✅ Position data (futures)');
    } else {
        lines.push('   ❌ Account balance (requires API key)');
        lines.push('   ❌ Holdings information (requires API key)');
        lines.push('   ❌ Open orders (requires API key)');
        lines.push('   ❌ Position data (requires API key)');
    }
    lines.push('');

    // Show errors if any
    if (validation.errors.length > 0) {
        lines.push('❌ Configuration Errors:');
        validation.errors.forEach(error => lines.push(`   ${error}`));
        lines.push('');
    }

    // Show warnings if any
    if (validation.warnings.length > 0) {
        lines.push('⚠️  Configuration Warnings:');
        validation.warnings.forEach(warning => lines.push(`   ${warning}`));
        lines.push('');
    }

    // Configuration help
    if (!validation.hasApiCredentials) {
        lines.push('📚 Quick Setup Guide:');
        lines.push('   1. Go to https://www.binance.com/en/my/settings/api-management');
        lines.push('   2. Create a new API key with "Read" permissions');
        lines.push('   3. Copy the API Key and Secret Key');
        lines.push('   4. Create a .env file in your project root:');
        lines.push('      BINANCE_API_KEY=your_api_key_here');
        lines.push('      BINANCE_API_SECRET=your_secret_key_here');
        lines.push('   5. Restart the MCP server');
        lines.push('');
        lines.push('🛡️  Security Note: Never share your API keys publicly!');
    }

    return lines.join('\n');
}
