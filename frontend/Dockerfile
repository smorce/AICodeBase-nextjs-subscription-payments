FROM node:20-alpine

# 必要なパッケージのインストール
RUN apk add --no-cache curl gnupg sudo

# GitHub CLIのインストール
RUN apk add --no-cache github-cli --repository=http://dl-cdn.alpinelinux.org/alpine/edge/testing

# Supabase CLIのインストール (バージョン 1.192.5)
RUN curl -L -o supabase.apk https://github.com/supabase/cli/releases/download/v1.192.5/supabase_1.192.5_linux_amd64.apk && \
    apk add --allow-untrusted supabase.apk && \
    rm supabase.apk

# Vercel CLIのインストール
RUN npm i -g vercel

# Stripe CLIのインストール
RUN curl -L -o stripe.tar.gz https://github.com/stripe/stripe-cli/releases/download/v1.21.5/stripe_1.21.5_linux_x86_64.tar.gz && \
    tar -xzf stripe.tar.gz -C /usr/local/bin && \
    rm stripe.tar.gz && \
    chmod +x /usr/local/bin/stripe

# pnpm のインストール
RUN npm install -g pnpm@9.10.0

# 作業ディレクトリの設定
WORKDIR /app

# パッケージファイルをコピー
COPY package.json pnpm-lock.yaml ./

# 依存関係のインストール
RUN pnpm install

# アプリケーションコードをコピー
COPY . .

# entrypoint.shをコピーして実行権限を付与
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ポートを公開
EXPOSE 3000

# エントリーポイントとCMDを設定
ENTRYPOINT ["/entrypoint.sh"]
CMD ["pnpm", "run", "dev", "--hostname", "0.0.0.0"]