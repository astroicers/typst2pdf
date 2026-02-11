FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y \
    curl unzip python3 python3-pip ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    fonts-noto fonts-noto-cjk fonts-linuxlibertine && \
    rm -rf /var/lib/apt/lists/*

# Install Typst CLI
RUN curl -L https://github.com/typst/typst/releases/download/v0.13.1/typst-x86_64-unknown-linux-musl.tar.xz \
    | tar -xJf - && mv typst-x86_64-unknown-linux-musl/typst /usr/local/bin/

WORKDIR /app
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app.py /app/

EXPOSE 8000
CMD ["python3", "app.py"]
