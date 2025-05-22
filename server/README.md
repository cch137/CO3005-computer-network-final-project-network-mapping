# Network Mapping Server 2025 April | 網路映射伺服器 2025 四月

## Overview | 概述

This project is a Flask-based server designed for network mapping and text embedding generation. It provides APIs for managing web pages, nodes, and generating embeddings for text data.

此專案是一個基於 Flask 的伺服器，用於網路映射和文字嵌入生成，提供管理網頁、節點以及生成文字數據嵌入的 API。

## Project Structure | 專案結構

- **`app.py`**
  - The entry point of the application and the main API handler. It manages endpoints for text embeddings (`/vectors`), retrieving unvisited pages and domains (`/cn-project/next-pages`, `/cn-project/next-domains`), and storing page and node data (`/cn-project/store-pages`, `/cn-project/store-nodes`).
  - 應用程式的入口點和主要 API 處理程序。管理文字嵌入端點（`/vectors`）、獲取未訪問頁面和域名（`/cn-project/next-pages`, `/cn-project/next-domains`）以及儲存頁面和節點數據（`/cn-project/store-pages`, `/cn-project/store-nodes`）。
- **`modules/`**
  - Contains custom modules for embeddings, schemas, database operations, and other functionalities that support the main application.
  - 包含支援主應用程式的自定義模組，包括嵌入、模式、數據庫操作等功能。

## Installation | 安裝

### Prerequisites | 前提條件

Python 3.8 or higher, Virtual environment (recommended)

Python 3.8 或更高版本，虛擬環境（推薦）

### Setup | 設置

1. **Clone the Repository | 克隆倉庫** (if applicable):

   ```bash
   git clone <repository-url>
   cd network-mapping-2025-april
   ```

2. **Create and Activate a Virtual Environment | 創建並啟用虛擬環境**:

   - **Windows**:
     ```bash
     .venv\Scripts\activate
     ```
   - **Linux/MacOS**:
     ```bash
     source .venv/bin/activate
     ```

3. **Install Dependencies | 安裝依賴項**:

   ```bash
   sudo apt update
   sudo apt install python3-dev libpq-dev build-essential
   pip install -r requirements.txt
   ```

   **Export Dependencies | 導出依賴項** (if needed):

   ```bash
   bash bin/exports
   ```

## Usage | 使用方法

### Running the Application | 運行應用程式

To start the server, run:

要啟動伺服器，請運行：

```bash
python app.py
```

The server will be available at `http://0.0.0.0:<PORT>` (port defined in constants).

伺服器將在 `http://0.0.0.0:<PORT>` （端口在常量中定義）上可用。

### API Endpoints | API 端點

- **GET `/`**
  - Returns a simple "OK" response to confirm the server is running.
  - 返回簡單的“OK”響應以確認伺服器正在運行。
- **POST `/vectors`**
  - Generates and returns CBOR-encoded text embeddings.
  - 生成並返回 CBOR 編碼的文字嵌入。
- **GET `/cn-project/next-pages`**
  - Retrieves a list of unvisited URLs for processing.
  - 獲取未訪問的 URL 列表以進行處理。
- **GET `/cn-project/next-domains`**
  - Retrieves a list of unvisited domains.
  - 獲取未訪問的域名列表。
- **POST `/cn-project/store-pages`**
  - Stores page metadata and processes content chunks.
  - 儲存頁面元數據並處理內容塊。
- **POST `/cn-project/store-nodes`**
  - Stores node metadata.
  - 儲存節點元數據。
