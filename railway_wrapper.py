#!/usr/bin/env python3
"""
Railway Wrapper for WhisperLive
Handles HTTP health checks AND WebSocket transcription
"""

import asyncio
import json
import logging
import os
import signal
import sys
from aiohttp import web, WSMsgType
from aiohttp.web_ws import WebSocketResponse
import subprocess
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RailwayWhisperLiveWrapper:
    def __init__(self, port=9090):
        self.port = port
        self.app = web.Application()
        self.whisper_server = None
        self.setup_routes()
        
    def setup_routes(self):
        """Setup HTTP and WebSocket routes"""
        # Health check endpoints for Railway
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_head('/health', self.health_check)
        self.app.router.add_get('/', self.websocket_handler)
        
    async def health_check(self, request):
        """HTTP health check endpoint for Railway"""
        logger.info(f"Health check: {request.method} {request.path}")
        return web.json_response({
            "status": "healthy",
            "service": "WhisperLive",
            "backend": "faster_whisper",
            "timestamp": time.time()
        })
    
    async def websocket_handler(self, request):
        """Handle WebSocket connections - proxy to WhisperLive"""
        # Check if this is a WebSocket upgrade request
        if request.headers.get('upgrade', '').lower() != 'websocket':
            # Regular HTTP request - return service info
            return web.json_response({
                "service": "WhisperLive WebSocket Server",
                "status": "running",
                "backend": "faster_whisper",
                "websocket_url": f"ws://localhost:{self.port}/"
            })
        
        # Handle WebSocket connection
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        logger.info("New WebSocket connection established")
        
        try:
            # Start WhisperLive server if not running
            await self.ensure_whisper_server()
            
            # Proxy WebSocket messages to WhisperLive
            await self.proxy_websocket(ws)
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await ws.close()
        finally:
            logger.info("WebSocket connection closed")
            
        return ws
    
    async def ensure_whisper_server(self):
        """Ensure WhisperLive server is running"""
        if self.whisper_server is None or self.whisper_server.poll() is not None:
            logger.info("Starting WhisperLive backend server...")
            self.whisper_server = subprocess.Popen([
                sys.executable, "run_server.py",
                "--port", "9091",  # Internal port
                "--backend", "faster_whisper"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it time to start
            await asyncio.sleep(3)
            logger.info("WhisperLive backend server started")
    
    async def proxy_websocket(self, client_ws):
        """Proxy WebSocket messages between client and WhisperLive"""
        import websockets
        
        try:
            # Connect to internal WhisperLive server
            async with websockets.connect("ws://localhost:9091") as server_ws:
                
                async def client_to_server():
                    try:
                        async for msg in client_ws:
                            if msg.type == WSMsgType.TEXT:
                                await server_ws.send(msg.data)
                            elif msg.type == WSMsgType.BINARY:
                                await server_ws.send(msg.data)
                            elif msg.type == WSMsgType.ERROR:
                                logger.error(f"WebSocket error: {client_ws.exception()}")
                                break
                    except Exception as e:
                        logger.error(f"Client to server error: {e}")
                
                async def server_to_client():
                    try:
                        async for msg in server_ws:
                            if isinstance(msg, str):
                                await client_ws.send_str(msg)
                            elif isinstance(msg, bytes):
                                await client_ws.send_bytes(msg)
                    except Exception as e:
                        logger.error(f"Server to client error: {e}")
                
                # Run both directions concurrently
                await asyncio.gather(
                    client_to_server(),
                    server_to_client(),
                    return_exceptions=True
                )
                
        except Exception as e:
            logger.error(f"Proxy error: {e}")
    
    def run(self):
        """Run the server"""
        logger.info(f"Starting Railway WhisperLive Wrapper on port {self.port}")
        web.run_app(self.app, host='0.0.0.0', port=self.port)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    sys.exit(0)

if __name__ == "__main__":
    # Handle shutdown gracefully
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get port from environment (Railway sets this)
    port = int(os.environ.get('PORT', 9090))
    
    # Create and run wrapper
    wrapper = RailwayWhisperLiveWrapper(port)
    wrapper.run() 