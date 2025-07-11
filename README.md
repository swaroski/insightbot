# InsightBot - AI-Powered Knowledge Platform

A production-ready end-to-end AI SaaS platform that allows users to query financial, technical, and business documents with AI-powered insights using LangGraph agent orchestration.

## 🚀 Features

- **LangGraph Agent Workflow**: Multi-step agentic LLM behavior with query parsing, retrieval, analysis, summary, and evaluation
- **OpenAI Integration**: Powered by GPT-4o for reasoning and text-embedding-ada-002 for embeddings
- **Vector Search**: FAISS-based document embedding and similarity search
- **Modern Frontend**: Next.js 14 with Tailwind CSS and shadcn/ui components
- **Document Processing**: Support for PDF, TXT, and DOCX files
- **Real-time Evaluation**: LLM-as-a-judge scoring for answer quality
- **Production Ready**: Docker containerization and CI/CD pipeline
- **Analytics**: Query history, performance metrics, and evaluation scores
- **MCP Server**: Model Context Protocol integration for AI assistants

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Vector Store  │
│   (Next.js)     │────│   (FastAPI)     │────│   (FAISS)       │
│   - Query UI    │    │   - LangGraph   │    │   - Embeddings  │
│   - Upload      │    │   - Agents      │    │   - Similarity  │
│   - Analytics   │    │   - Evaluation  │    │   - Retrieval   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   MCP Server    │
                    │   (Protocol)    │
                    │   - Tools       │
                    │   - Integration │
                    │   - AI Assistant│
                    └─────────────────┘
```

### Agent Workflow

1. **Query Parser Agent**: Extracts intent, entities, and query type
2. **Retriever Agent**: Searches FAISS vector store for relevant documents
3. **Analysis Agent**: Performs reasoning over retrieved content using GPT-4o
4. **Summary Agent**: Creates final answer with citations and key points
5. **Evaluation Agent**: Scores output quality using LLM-as-a-judge

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **LangGraph**: Agent workflow orchestration
- **FAISS**: Vector similarity search
- **OpenAI**: GPT-4o and text-embedding-ada-002
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Production database
- **Redis**: Caching and session storage

### Frontend
- **Next.js 14**: React framework with App Router
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: Modern UI components
- **Framer Motion**: Animation library
- **SWR**: Data fetching and caching
- **TypeScript**: Type safety

### DevOps
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline
- **Vercel**: Frontend deployment
- **Fly.io**: Backend deployment

## 📦 Installation

### Prerequisites
- Docker and Docker Compose
- Node.js 18+
- Python 3.11+
- OpenAI API key

### Quick Start with Docker

1. **Clone the repository**
```bash
git clone https://github.com/your-username/insightbot.git
cd insightbot
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

3. **Start the services**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/insightbot

# Application Configuration
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# File Upload Configuration
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# FAISS Configuration
FAISS_INDEX_PATH=./faiss_index
EMBEDDING_MODEL=text-embedding-ada-002

# Evaluation Configuration
EVALUATION_MODEL=gpt-4o-mini
EVALUATION_THRESHOLD=3.0

# Security
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=http://localhost:3000
```

## 📚 API Documentation

### Core Endpoints

#### Query Documents
```http
POST /api/query
Content-Type: application/json

{
  "query": "Compare Tesla and NVIDIA performance in 2023",
  "session_id": "optional-session-id"
}
```

#### Upload Documents
```http
POST /api/upload
Content-Type: multipart/form-data

file: <PDF/TXT/DOCX file>
```

#### Get Query History
```http
GET /api/queries?page=1&page_size=10&session_id=optional
```

#### Re-evaluate Query
```http
POST /api/eval
Content-Type: application/json

{
  "query_id": "query-uuid"
}
```

### Response Format

```json
{
  "query": "User's question",
  "answer": "AI-generated answer with citations",
  "sources": [
    {
      "content": "Relevant text snippet",
      "filename": "document.pdf",
      "page": 1,
      "relevance_score": 0.95
    }
  ],
  "evaluation": {
    "score": 4.2,
    "rationale": "Well-structured answer with good sources",
    "criteria": {
      "accuracy": 4.5,
      "completeness": 4.0,
      "relevance": 4.3,
      "clarity": 4.1,
      "coherence": 4.2
    }
  },
  "session_id": "session-uuid",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
docker-compose -f docker-compose.test.yml up --build
```

## 🚀 Deployment

### Production Deployment with Docker

1. **Build and push images**
```bash
docker build -f docker/Dockerfile.backend -t insightbot-backend .
docker build -f docker/Dockerfile.frontend -t insightbot-frontend .
```

2. **Deploy with Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment

#### Vercel (Frontend)
```bash
cd frontend
vercel --prod
```

#### Fly.io (Backend)
```bash
fly deploy -f fly.toml
```

#### AWS ECS
Use the provided `docker-compose.yml` with AWS ECS CLI or create ECS task definitions.

## 📊 Monitoring and Analytics

### Available Metrics
- Query volume and patterns
- Response evaluation scores
- Document processing statistics
- Agent execution times
- Error rates and types

### Health Checks
- **Backend**: `GET /health`
- **Database**: Connection status
- **Vector Store**: Index status
- **OpenAI**: API connectivity

## 🔐 Security

- **API Keys**: Securely stored in environment variables
- **File Uploads**: Type and size validation
- **CORS**: Configured for specific origins
- **Rate Limiting**: Implemented for API endpoints
- **Input Validation**: Pydantic models for request validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit a pull request

### Code Style
- **Backend**: Black formatting, Ruff linting
- **Frontend**: Prettier formatting, ESLint
- **Commits**: Conventional commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint for API documentation
- **Issues**: Create an issue on GitHub
- **Discord**: Join our Discord community

## 🚀 Roadmap

- [ ] Multi-user authentication with Supabase
- [ ] Real-time chat interface
- [ ] Advanced analytics dashboard
- [ ] Mobile app support
- [ ] Enterprise features (SSO, audit logs)
- [ ] Multi-language support
- [ ] Advanced evaluation metrics

## 📈 Performance

- **Query Response**: < 5 seconds average
- **File Processing**: < 30 seconds for 10MB documents
- **Concurrent Users**: 100+ supported
- **Uptime**: 99.9% target

## 🔗 MCP Server Integration

InsightBot includes a Model Context Protocol (MCP) server for seamless integration with AI assistants like Claude Code.

### Quick Start

```bash
# Start MCP server with Docker
docker-compose up mcp-server

# Or run locally
python -m mcp_server.main
```

### Available Tools

- **query_documents**: Query documents using AI workflow
- **upload_document**: Upload and process documents
- **get_document_stats**: Get collection statistics
- **search_similar_documents**: Find similar documents
- **get_query_history**: Retrieve query history
- **evaluate_response**: Evaluate response quality

### Claude Code Integration

Add to your `~/.claude-code/settings.json`:

```json
{
  "mcpServers": {
    "insightbot": {
      "command": "python",
      "args": ["-m", "mcp_server.main"],
      "cwd": "/path/to/insightbot/backend",
      "env": {
        "OPENAI_API_KEY": "your-api-key"
      }
    }
  }
}
```

For detailed MCP integration guide, see [MCP_INTEGRATION.md](MCP_INTEGRATION.md).

---

Built with ❤️ by the InsightBot team. Powered by OpenAI, LangGraph, and modern web technologies.