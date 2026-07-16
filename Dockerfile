# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_GOOGLE_CLIENT_ID
ENV VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID
RUN npm run build

# Stage 2: Production backend + static files
FROM python:3.12-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Copy built frontend into static directory
COPY --from=frontend-build /app/frontend/dist ./static

EXPOSE 8000

# --proxy-headers + --forwarded-allow-ips: no Railway o app fica atras de um proxy;
# sem isso request.client.host seria o IP do proxy e o rate limiting (CR-044) trataria
# todos os usuarios como um so. O container so e acessivel via proxy do Railway, entao
# confiar no peer imediato ("*") e seguro.
CMD ["sh", "-c", "alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"]
