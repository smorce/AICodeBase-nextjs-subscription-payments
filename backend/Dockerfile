FROM python:3.12.3-slim

# ビルド時の引数を定義
ARG UID=1002
ARG GID=1002

# ユーザーとグループを作成
RUN addgroup --gid $GID appgroup && \
    adduser --disabled-password --gecos "" --uid $UID --gid $GID appuser

# システムパッケージを更新し、bash と WeasyPrint の依存関係をインストール
# md2pdf を使うためにここで WeasyPrint の依存関係をインストールする必要がある(pip install するだけでは不十分)
# Chromium のインストール直後に which chromium コマンドを実行してパスを確認し、それに合わせてCHROME_PATHを設定する
RUN apt-get update && apt-get install -y \
    bash \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    curl \
    chromium \
    && rm -rf /var/lib/apt/lists/* \
    && CHROME_PATH=$(which chromium) \
    && echo "export CHROME_PATH=$CHROME_PATH" >> /root/.bashrc

# Node.jsとnpmをインストール
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g npm@latest

# Marp CLI v4.0.0 をグローバルにインストール
RUN npm i -g @marp-team/marp-cli@4.0.0

WORKDIR /app

# ビルド時間を短縮するためにアプリケーションコードをコピーする前にライブラリをインストールする
COPY requirements.txt /app/

# Pythonの依存関係をインストール
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー。このCOPY命令より後のコマンドは、
# アプリケーションコードに変更があった場合のみ再実行する
COPY . /app

# スクリプトの所有権をappuserに変更し、実行権限を付与
RUN chown -R appuser:appgroup /app && \
    chmod +x /app/entrypoint.sh

# Chromiumのパスを環境変数として設定
# ENV CHROME_PATH=$CHROME_PATH は冗長に見えるかもしれませんが、RUNコマンドで設定した環境変数は、そのRUNレイヤー内でのみ有効です。後続のレイヤーでCHROME_PATHを使用するためには、ENVで設定する必要があります。
ENV CHROME_PATH=$CHROME_PATH

# デフォルトユーザーを設定
USER appuser

# エントリーポイント
ENTRYPOINT ["./entrypoint.sh"]