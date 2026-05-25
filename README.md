# PDF RAG Chatbot v2.0 🤖

A production-ready full-stack application for interactive PDF Q&A using RAG (Retrieval-Augmented Generation) with LangChain, FastAPI, and React.

## Features

✨ **Core Features**
- Upload and process PDF documents
- Ask questions about PDFs using AI
- Hybrid retrieval (BM25 + semantic search via FAISS)
- Real-time chat with conversation history
- Multiple document support via sessions
- Production-ready with health checks and rate limiting

🛡️ **Production Ready**
- Comprehensive logging and error handling
- Health check endpoints for monitoring
- Rate limiting (5 req/min for uploads, 10 req/min for questions)
- CORS security configuration
- Docker support with frontend bundling
- Input validation and sanitization
- Graceful shutdown handling

⚡ **Performance**
- Lazy loading of ML models for fast startup
- Vite for optimized frontend bundles
- Efficient PDF processing pipeline
- Session-based caching

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Local Development

**1. Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Copy environment template and add your API key
cp .env.example .env
# Edit .env and add your GROQ_API_KEY from https://console.groq.com

pip install -r requirements.txt
python main.py
```

Backend runs on: `http://localhost:8000`

**2. Frontend Setup** (in new terminal)
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on: `http://localhost:5173`

**3. API Documentation**
Open `http://localhost:8000/docs` in your browser.

### Docker Deployment

```bash
# Build image
docker build -t pdf-rag-chatbot .

# Run container
docker run -d \
  --name chatbot \
  -e GROQ_API_KEY=your_key_here \
  -e ENVIRONMENT=production \
  -p 8000:8000 \
  pdf-rag-chatbot
```

**Using Docker Compose**
```bash
docker-compose up -d
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check for monitoring |
| GET | `/ready` | Readiness check with session count |
| POST | `/upload` | Upload PDF document |
| POST | `/ask` | Ask question about uploaded PDF |
| GET | `/history/{session_id}` | Get chat history |
| GET | `/sessions` | List all active sessions |
| DELETE | `/session/{session_id}` | Delete session |

### Example Usage

**Upload PDF**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

Response:
```json
{
  "session_id": "abc12345",
  "filename": "document.pdf",
  "total_chunks": 42,
  "total_pages": 10
}
```

**Ask Question**
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc12345",
    "question": "What is the main topic?"
  }'
```

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application
│   ├── rag_engine.py        # RAG pipeline implementation
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   └── runtime.txt          # Python version
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── main.jsx         # Entry point
│   │   └── App.css          # Styles
│   ├── package.json         # Node dependencies
│   ├── vite.config.js       # Vite configuration
│   └── .env.example         # Frontend env template
│
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Docker Compose setup
├── netlify.toml            # Netlify configuration
└── PRODUCTION_DEPLOYMENT.md # Deployment guide
```

## Configuration

### Environment Variables

**Backend (.env)**
```env
# Required
GROQ_API_KEY=your_key_here

# Optional
ENVIRONMENT=production              # development or production
CORS_ORIGINS=https://yourdomain.com # Comma-separated allowed origins
PORT=8000                          # Server port
CHUNK_SIZE=500                     # PDF chunk size
LLM_TEMPERATURE=0.1                # LLM temperature (0-1)
```

See [backend/.env.example](backend/.env.example) for all options.

**Frontend (.env)**
```env
VITE_API_URL=http://localhost:8000  # Backend API URL
```

## Rate Limiting

- **Upload endpoint**: 5 requests per minute per IP
- **Ask endpoint**: 10 requests per minute per IP
- **Max file size**: 50MB

## Performance Optimizations

- ✅ Lazy loading of ML models
- ✅ Vite + React 19 for fast frontend
- ✅ Session-based caching
- ✅ Efficient PDF text extraction
- ✅ Hybrid search (BM25 + semantic)
- ✅ Minified production builds

## Deployment

### Render.com
```bash
git push origin main  # Automatically deploys
```
Configure in Render dashboard:
- Set `ENVIRONMENT=production`
- Add `GROQ_API_KEY` secret
- Set `CORS_ORIGINS` to your domain

### Railway.app
Push to GitHub, configure env vars in Railway dashboard.

### Hugging Face Spaces
Create Docker Space, connect GitHub repo.

### Docker
Build and run on any cloud provider (AWS, DigitalOcean, etc.).

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) for detailed deployment guide.

## Health Monitoring

Check service health:
```bash
# Basic health
curl http://localhost:8000/health

# Detailed readiness
curl http://localhost:8000/ready

# Check logs (Docker)
docker logs chatbot -f
```

## Troubleshooting

**CORS errors?**
- Verify `CORS_ORIGINS` includes your frontend URL
- Restart backend after changing settings

**API key issues?**
- Check `GROQ_API_KEY` is set in `.env`
- Verify key from https://console.groq.com

**PDF upload fails?**
- File size max 50MB
- Ensure valid PDF format

**Out of memory?**
- Clear old sessions: `DELETE /session/{id}`
- Reduce `CHUNK_SIZE` for large PDFs

## Development

### Running Tests
```bash
cd backend
pytest
```

### Code Formatting
```bash
# Backend
black backend/
pylint backend/

# Frontend
npm run lint
```

### Building for Production
```bash
# Frontend
cd frontend
npm run build

# Docker
docker build -t pdf-rag-chatbot:latest .
```

## Security Best Practices

⚠️ **Important**
- ✅ Never commit `.env` with real API keys
- ✅ Use `ENVIRONMENT=production` in production
- ✅ Enable HTTPS for all deployments
- ✅ Keep API keys in environment variables only
- ✅ Regularly monitor API logs
- ✅ Use strong CORS origins

## Technologies

**Backend**
- FastAPI - Modern Python web framework
- LangChain - LLM framework and tools
- FAISS - Semantic search indexing
- BM25 - Keyword search
- Groq API - Fast LLM inference
- PyPDF2 - PDF processing

**Frontend**
- React 19 - UI library
- Vite - Build tool
- Lucide React - Icons
- Axios - HTTP client

**Deployment**
- Docker - Containerization
- Netlify - Frontend hosting
- Render/Railway - Backend hosting

## License

MIT

## Support

For issues or questions:
1. Check [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
2. Review API docs: `http://localhost:8000/docs`
3. Check backend logs: `docker logs chatbot`

## Future Enhancements

- [ ] User authentication
- [ ] Database for persistent storage
- [ ] Redis caching
- [ ] Multiple LLM providers
- [ ] Advanced analytics
- [ ] Feedback system
- [ ] Document management
- [ ] Conversation sharing

---

**Built with ❤️ using FastAPI, React, and LangChain**
