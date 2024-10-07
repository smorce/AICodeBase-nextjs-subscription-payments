FROM python:3.12.3-slim

# ビルド時の引数を定義
ARG UID=1002
ARG GID=1002

# ユーザーとグループを作成
RUN addgroup --gid $GID appgroup && \
    adduser --disabled-password --gecos "" --uid $UID --gid $GID appuser

# システムパッケージを更新し、bash と WeasyPrint の依存関係をインストール
# md2pdf を使うためにここで WeasyPrint の依存関係をインストールする必要がある(pip install するだけでは不十分)
RUN apt-get update && apt-get install -y \
    bash \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# アプリケーションコードをコピー
COPY . /app

# Pythonの依存関係をインストール
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
# sentence-transformers がかなり重たいので、これだけ requirements.txt から切り出してキャッシュする
RUN pip install langchain-huggingface==0.1.0

# スクリプトの所有権をappuserに変更し、実行権限を付与
RUN chown -R appuser:appgroup /app && \
    chmod +x /app/entrypoint.sh

# デフォルトユーザーを設定
USER appuser

# エントリーポイント
ENTRYPOINT ["./entrypoint.sh"]