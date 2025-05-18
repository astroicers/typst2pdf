FROM debian:bullseye-slim

# 安裝 typst 與 python 環境
RUN apt-get update && apt-get install -y \
    curl unzip python3 python3-pip ca-certificates && \
    pip3 install flask && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    fonts-noto fonts-noto-cjk fonts-linuxlibertine

# 安裝 Typst CLI
RUN curl -L https://github.com/typst/typst/releases/download/v0.13.1/typst-x86_64-unknown-linux-musl.tar.xz \
    | tar -xJf - && mv typst-x86_64-unknown-linux-musl/typst /usr/local/bin/

WORKDIR /app
COPY app.py /app

EXPOSE 8000
CMD ["python3", "app.py"]
