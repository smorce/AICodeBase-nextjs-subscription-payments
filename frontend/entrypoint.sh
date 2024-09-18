#!/bin/sh
set -e

# GitHub認証をシークレットから読み込む（読み込む必要はないかもしれない）
if [ -f /run/secrets/github_token ]; then
  gh auth login --with-token < /run/secrets/github_token
else
  echo "GitHubトークンがシークレットとして提供されていません。認証をスキップします。"
fi

# Supabase認証とプロジェクトリンク
if [ -n "$SUPABASE_ACCESS_TOKEN" ] && [ -n "$SUPABASE_REFERENCE_ID" ] && [ -n "$SUPABASE_DB_PASSWORD" ]; then
  supabase login "$SUPABASE_ACCESS_TOKEN"
  supabase link --project-ref "$SUPABASE_REFERENCE_ID" -p "$SUPABASE_DB_PASSWORD"
elif [ -n "$SUPABASE_ACCESS_TOKEN" ]; then
  supabase login "$SUPABASE_ACCESS_TOKEN"
  echo "Supabase project reference or database password not set. Skipping project link."
else
  echo "SUPABASE_ACCESS_TOKEN is not set. Skipping Supabase authentication and project link."
fi

# Vercel認証（必要に応じて）
# if [ -n "$VERCEL_TOKEN" ]; then
#   vercel login --token "$VERCEL_TOKEN"
# fi

# Stripe認証（必要に応じて）
# if [ -n "$STRIPE_API_KEY" ]; then
#   stripe login --api-key "$STRIPE_API_KEY"
# fi

# 元のコマンドを実行
exec "$@"