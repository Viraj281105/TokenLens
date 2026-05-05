# ============================================================
# TokenLens — Multi-Stage Dockerfile
# ============================================================
# Stage 1: Build Next.js frontend (static export)
# Stage 2: Python backend with built frontend
# ============================================================

# ── Stage 1: Build Frontend ─────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies first (cache layer)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --production=false

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python Backend + Static Frontend ───────────────────
FROM python:3.11-slim AS production

# Security: create non-root user
RUN groupadd -r tokenlens && useradd -r -g tokenlens -s /bin/false tokenlens

# System dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cache layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/frontend/out ./frontend/out

# Create data directory with proper permissions
RUN mkdir -p /app/data && \
    mkdir -p /home/tokenlens/.cache/huggingface && \
    chown -R tokenlens:tokenlens /app && \
    chown -R tokenlens:tokenlens /home/tokenlens

# Pre-download the sentence-transformers model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Environment
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV LOG_LEVEL=INFO

# Switch to non-root user
USER tokenlens

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Start uvicorn
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
