# WhisperLive Railway Deployment Guide

This guide will help you deploy WhisperLive to Railway for stable, cloud-hosted speech-to-text transcription.

## 🚀 Quick Deploy to Railway

### Step 1: Prepare Repository
The deployment files are already created:
- ✅ `requirements.txt` - Python dependencies
- ✅ `railway.json` - Railway configuration
- ✅ `Procfile` - Startup command

### Step 2: Deploy to Railway

**Option A: One-Click Deploy**
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/WhisperLive)

**Option B: Manual Deploy**
1. Go to [railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Connect your GitHub account and select this WhisperLive repository
4. Railway will automatically detect Python and deploy using our configuration

### Step 3: Configure Environment (Optional)
In Railway dashboard, you can set these environment variables:
- `WHISPER_MODEL` - Model to use (default: small)
- `MAX_CLIENTS` - Maximum concurrent clients (default: 4)
- `MAX_CONNECTION_TIME` - Max connection time in seconds (default: 600)

### Step 4: Get Your Railway URL
After deployment, Railway will provide a URL like:
`https://your-app-name.railway.app`

## 🔧 Update Church Translator Configuration

Update your `.env` file in ChurchTranslator:
```env
WHISPERLIVE_HOST=your-app-name.railway.app
WHISPERLIVE_PORT=443
```

Or use the configuration function to point to your Railway deployment.

## ✅ Benefits

- **Always Online**: 24/7 availability
- **Auto-scaling**: Handles multiple users
- **Monitoring**: Built-in health checks
- **SSL**: Secure HTTPS connections
- **No Local Setup**: No need to run Python server locally

## 🔍 Monitoring

Check your deployment:
- Railway Dashboard: Monitor CPU, memory, logs
- Health Check: `https://your-app-name.railway.app/health`
- WebSocket Test: Connect to `wss://your-app-name.railway.app`

## 💰 Cost

Railway offers:
- **Free Tier**: $5 credit monthly (good for development)
- **Pro Plan**: $20/month for production use
- **Usage-based**: Pay only for what you use

## 🔧 Troubleshooting

### Common Issues:

**1. WebSocket Health Check Errors**
If you see `InvalidUpgrade: invalid Connection header: close` errors:
- This is normal - Railway's health checks use HTTP, but WhisperLive is WebSocket-only
- The server will still work for WebSocket connections
- Health checks are disabled in our configuration to avoid false failures

**2. Deployment Fails**
If deployment fails:
- Check Railway logs in the dashboard
- Verify requirements.txt has all needed packages
- Ensure run_server.py accepts --port argument
- Try redeploying with "Force rebuild"

**3. Model Download Issues**
If models fail to download:
- Railway has limited memory during build
- The "small" model should work fine
- Larger models may require Railway Pro plan

**4. Connection Issues**
If Church Translator can't connect:
- Verify Railway URL is correct (https://your-app.railway.app)
- Use WSS (secure WebSocket) not WS
- Check Railway deployment logs for errors

### Checking Logs
```bash
# In Railway dashboard:
1. Go to your project
2. Click "Deployments"
3. Click on the latest deployment
4. View logs to debug issues
```

## 🎯 Next Steps

Once deployed:
1. Update Church Translator to use Railway URL
2. Test transcription with your React Native app
3. Consider upgrading to custom fine-tuned model
4. Monitor usage and performance in Railway dashboard 