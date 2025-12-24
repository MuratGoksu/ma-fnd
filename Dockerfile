FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Download spaCy language model (optional)
# RUN python -m spacy download en_core_web_sm
# RUN python -m spacy download tr_core_news_sm

# Expose API port
EXPOSE 8000

# Run API
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

