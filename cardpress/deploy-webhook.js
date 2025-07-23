#!/usr/bin/env node

/**
 * CardPress Deploy Webhook Server
 * 
 * This script creates a simple HTTP server that listens for deployment
 * webhooks from the CardPress UI deploy button and triggers the deploy script.
 * 
 * Usage:
 *   node deploy-webhook.js [port]
 * 
 * Environment Variables:
 *   WEBHOOK_SECRET - Optional secret for webhook authentication
 *   DEPLOY_SCRIPT_PATH - Path to deploy.sh (default: ./deploy.sh)
 *   DEPLOY_PLATFORM - Platform to deploy to (1-7, default: 4 for Cloudflare Pages)
 */

const http = require('http');
const { spawn } = require('child_process');
const path = require('path');

// Configuration
const PORT = process.argv[2] || process.env.PORT || 3000;
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET;
const DEPLOY_SCRIPT_PATH = process.env.DEPLOY_SCRIPT_PATH || './deploy.sh';
const DEPLOY_PLATFORM = process.env.DEPLOY_PLATFORM || '4'; // Cloudflare Pages by default

console.log('🚀 CardPress Deploy Webhook Server');
console.log('==================================');
console.log(`📡 Listening on port: ${PORT}`);
console.log(`📝 Deploy script: ${DEPLOY_SCRIPT_PATH}`);
console.log(`🌐 Default platform: ${DEPLOY_PLATFORM}`);
if (WEBHOOK_SECRET) {
    console.log('🔐 Webhook authentication: enabled');
}
console.log('');

// Create HTTP server
const server = http.createServer(async (req, res) => {
    // Enable CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Health check endpoint
    if (req.method === 'GET' && req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'healthy',
            timestamp: new Date().toISOString(),
            uptime: process.uptime()
        }));
        return;
    }

    // Deploy webhook endpoint
    if (req.method === 'POST' && (req.url === '/webhook/deploy' || req.url === '/deploy')) {
        try {
            // Parse request body
            let body = '';
            req.on('data', chunk => {
                body += chunk.toString();
            });

            req.on('end', async () => {
                try {
                    const payload = body ? JSON.parse(body) : {};
                    
                    // Check webhook secret if configured
                    if (WEBHOOK_SECRET) {
                        const authHeader = req.headers.authorization;
                        const providedSecret = req.headers['x-webhook-secret'] || payload.secret;
                        
                        if (providedSecret !== WEBHOOK_SECRET) {
                            console.log('❌ Unauthorized webhook attempt');
                            res.writeHead(401, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({ error: 'Unauthorized' }));
                            return;
                        }
                    }

                    console.log('📨 Deploy webhook received:', {
                        trigger: payload.trigger || 'webhook',
                        postsCount: payload.postsCount || 'unknown',
                        timestamp: payload.timestamp || new Date().toISOString()
                    });

                    // Determine platform
                    const platform = payload.platform || DEPLOY_PLATFORM;

                    // Execute deploy script
                    console.log(`🚀 Starting deployment to platform ${platform}...`);
                    
                    const deployProcess = spawn('bash', [DEPLOY_SCRIPT_PATH, platform], {
                        cwd: path.dirname(path.resolve(DEPLOY_SCRIPT_PATH)),
                        stdio: ['ignore', 'pipe', 'pipe']
                    });

                    let stdout = '';
                    let stderr = '';

                    deployProcess.stdout.on('data', (data) => {
                        const output = data.toString();
                        stdout += output;
                        console.log(output.trim());
                    });

                    deployProcess.stderr.on('data', (data) => {
                        const output = data.toString();
                        stderr += output;
                        console.error(output.trim());
                    });

                    deployProcess.on('close', (code) => {
                        if (code === 0) {
                            console.log('✅ Deployment completed successfully');
                            res.writeHead(200, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({
                                success: true,
                                message: 'Deployment completed successfully',
                                platform: platform,
                                timestamp: new Date().toISOString()
                            }));
                        } else {
                            console.log(`❌ Deployment failed with exit code ${code}`);
                            res.writeHead(500, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({
                                success: false,
                                message: 'Deployment failed',
                                exitCode: code,
                                stderr: stderr.trim(),
                                timestamp: new Date().toISOString()
                            }));
                        }
                    });

                    deployProcess.on('error', (error) => {
                        console.error('❌ Failed to start deployment:', error);
                        res.writeHead(500, { 'Content-Type': 'application/json' });
                        res.end(JSON.stringify({
                            success: false,
                            message: 'Failed to start deployment',
                            error: error.message,
                            timestamp: new Date().toISOString()
                        }));
                    });

                    // Respond immediately that deployment started
                    res.writeHead(202, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: true,
                        message: 'Deployment started',
                        platform: platform,
                        timestamp: new Date().toISOString()
                    }));

                } catch (error) {
                    console.error('❌ Error processing webhook:', error);
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    res.end(JSON.stringify({
                        success: false,
                        message: 'Invalid webhook payload',
                        error: error.message
                    }));
                }
            });

        } catch (error) {
            console.error('❌ Webhook error:', error);
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                success: false,
                message: 'Internal server error',
                error: error.message
            }));
        }
        return;
    }

    // 404 for other routes
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
        error: 'Not found',
        endpoints: {
            'GET /health': 'Health check',
            'POST /webhook/deploy': 'Deploy webhook',
            'POST /deploy': 'Deploy webhook (alias)'
        }
    }));
});

// Start server
server.listen(PORT, () => {
    console.log(`✅ Webhook server running on http://localhost:${PORT}`);
    console.log('');
    console.log('Webhook endpoints:');
    console.log(`📡 POST http://localhost:${PORT}/webhook/deploy`);
    console.log(`📡 POST http://localhost:${PORT}/deploy`);
    console.log(`❤️  GET  http://localhost:${PORT}/health`);
    console.log('');
    console.log('Example webhook payload:');
    console.log('  {');
    console.log('    "trigger": "ui-deploy",');
    console.log('    "postsCount": 3,');
    console.log('    "platform": "4",');
    console.log('    "timestamp": "2024-01-01T12:00:00Z"');
    console.log('  }');
    console.log('');
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n🛑 Shutting down webhook server...');
    server.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
    });
});

process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM, shutting down...');
    server.close(() => {
        console.log('✅ Server closed');
        process.exit(0);
    });
}); 