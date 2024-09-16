FROM node:20-alpine

# pnpm のインストール
RUN npm install -g pnpm@9.10.0

WORKDIR /app

# パッケージファイルをコピー
COPY package.json pnpm-lock.yaml ./

# 依存関係の強制インストール（ロックファイルを更新せず）
RUN pnpm install --frozen-lockfile --force

# アプリケーションコードをコピー
COPY . .

# ポートを公開
EXPOSE 3000

# 起動コマンドを修正
CMD ["pnpm", "run", "dev", "--", "--hostname", "0.0.0.0"]