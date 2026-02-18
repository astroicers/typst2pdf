FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    curl fonts-noto fonts-noto-cjk fonts-linuxlibertine && \
    rm -rf /var/lib/apt/lists/*

# Install Typst CLI (for /fonts endpoint only; compilation uses typst-py)
RUN curl -L https://github.com/typst/typst/releases/download/v0.13.1/typst-x86_64-unknown-linux-musl.tar.xz \
    | tar -xJf - && mv typst-x86_64-unknown-linux-musl/typst /usr/local/bin/ && \
    rm -rf typst-x86_64-unknown-linux-musl

# Create non-root user
RUN useradd -m -s /bin/bash appuser

WORKDIR /app

# Copy package files
COPY pyproject.toml /app/
COPY src/ /app/src/

# Install package
RUN pip install --no-cache-dir .

USER appuser
EXPOSE 8000

# Use the installed CLI entry point
CMD ["typst-api"]
