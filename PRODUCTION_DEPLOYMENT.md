# Production Deployment Guide

## Prerequisites

- Docker installed
- Docker Hub account (or other container registry)
- Environment variables configured (see `.env.example`)
- Node.js 18+ and Python 3.11+ for local development

## Quick Start

### Local Development

1. **Set up backend**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your GROQ_API_KEY
   python main.py
   ```

2. **Set up frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Visit `http://localhost:5173` for the frontend and `http://localhost:8000` for API.

### Environment Variables

**Required:**
- `GROQ_API_KEY` - Get from https://console.groq.com

**Optional but recommended for production:**
- `ENVIRONMENT=production` - Hides Swagger docs, disables debug mode
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `PORT` - Server port (default: 8000)

See [.env.example](backend/.env.example) for all options.

## Docker Deployment

### Build Docker Image

```bash
docker build -t pdf-rag-chatbot:latest .
```

### Run Docker Container

```bash
docker run -d \
  --name chatbot \
  -e GROQ_API_KEY=your_key_here \
  -e ENVIRONMENT=production \
  -e PORT=8000 \
  -p 8000:8000 \
  pdf-rag-chatbot:latest
```

### Check Health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Deployment Platforms

### Render.com

1. Push code to GitHub
2. Create new Web Service on Render
3. Connect GitHub repo
4. Set environment variables in Render dashboard
5. Deploy

### Railway.app

1. Connect GitHub repo
2. Set environment variables
3. Deploy automatically on each push

### Hugging Face Spaces

1. Push code to GitHub
2. Create new Space (Docker)
3. Connect GitHub repo
4. Set secrets (GROQ_API_KEY, etc.)

### Netlify (Frontend Only)

Frontend is now bundled with backend. No separate deployment needed.

## Health Checks

The API provides health check endpoints for monitoring:

- `GET /health` - Basic health status
- `GET /ready` - Readiness check (includes session count)
- `GET /docs` - Swagger documentation (development only)

## API Rate Limiting

- Upload endpoint: 5 requests/minute per IP
- Ask endpoint: 10 requests/minute per IP

## Security Best Practices

1. ✅ Never commit `.env` with real keys
2. ✅ Set `ENVIRONMENT=production` in production
3. ✅ Use HTTPS in production
4. ✅ Keep API keys in environment variables only
5. ✅ Use strong CORS origins
6. ✅ Monitor API logs regularly
7. ✅ Set up backups for session data

## Monitoring

### View Logs

```bash
# Docker container logs
docker logs chatbot -f

# Check container health
docker inspect --format='{{json .State.Health}}' chatbot
```

### Metrics to Monitor

- Request latency (target: < 2 seconds)
- Error rate (target: < 1%)
- CPU and memory usage
- Active sessions
- API uptime

## Troubleshooting

### API returns 503 (Service Unavailable)

```bash
# Check readiness
curl http://localhost:8000/ready
```

### CORS errors in frontend

- Verify `CORS_ORIGINS` includes your frontend URL
- Restart backend after changing CORS settings

### Out of memory errors

- Limit sessions per container (current: unlimited)
- Use session cleanup or database storage (future: implement)

### PDF upload fails

- Check file size (max: 50MB)
- Verify file is valid PDF
- Check GROQ_API_KEY is set

## Performance Optimization

1. **Frontend**: Uses Vite for fast builds and optimized bundles
2. **Backend**: Lazy loads ML models to reduce startup time
3. **Embeddings**: Uses lightweight sentence-transformers model
4. **Caching**: Sessions stored in memory (consider Redis for scaling)

## Next Steps for Production

- [ ] Add database for persistent session storage
- [ ] Implement Redis for caching and session management
- [ ] Add authentication/user system
- [ ] Set up error tracking (Sentry)
- [ ] Configure CDN for static assets
- [ ] Add comprehensive monitoring/alerting
- [ ] Implement automatic session cleanup
- [ ] Add usage analytics
- [ ] Set up CI/CD pipeline

## Support

For issues or questions, check:
- Backend logs: `docker logs chatbot`
- API documentation: `http://localhost:8000/docs`
- Error messages in browser console
