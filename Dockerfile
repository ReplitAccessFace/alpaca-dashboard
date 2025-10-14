# Multi-stage build for production
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend
COPY package*.json ./
RUN npm ci --only=production
COPY src/ ./
RUN npm run build

FROM python:3.9-slim AS backend

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /app/frontend/build ./static

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["python", "main.py"]
