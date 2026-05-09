FROM python:3.13-slim

# Install uv and nanobot-ai
RUN pip install --no-cache-dir uv nanobot-ai

WORKDIR /app

# Install Python dependencies (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Copy project
COPY . .

# Data volume for SQLite db and memory_store
ENV DATA_DIR=/data
VOLUME /data

ENTRYPOINT ["./start.sh"]
