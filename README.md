# README

這份文件介紹如何建置並執行 Typst API 容器，並提供測試 API 的方法。以下所有內容均保留原有資訊，並整理重寫如下：

## 建立與執行容器

使用以下指令來建立 Docker 映像檔並啟動容器：
  
```bash
docker build -t typst-api .
docker run -p 38000:8000 typst-api
```

## 測試 API

使用 API 渲染 PDF 時注意以下事項：

- entrypoint 預設為 main.typ

透過 curl 指令送出請求：
  
```bash
cd example_zip
zip -r example.zip ./*
curl -X POST http://localhost:38000/render \
  -F "file=@example.zip" \
  -F "entrypoint=main.typ" \
  --output report.pdf
```

## 檢視容器中的所有字體

可透過 Typst CLI 指令列出容器內所有字體：
  
```bash
typst fonts
```
