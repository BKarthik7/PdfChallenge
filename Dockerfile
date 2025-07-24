# Use Python 3.9 slim image for AMD64 architecture
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir \
    PyMuPDF==1.23.8 \
    nltk==3.8.1 \
    scikit-learn==1.3.2 \
    numpy==1.24.3 \
    scipy==1.10.1

# Download NLTK data (if needed)
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set permissions
RUN chmod +x /app/main.py

# Default command - runs Round 1A by default
CMD ["python", "main.py", "--round", "1a", "--input-dir", "/app/input", "--output-dir", "/app/output"]
