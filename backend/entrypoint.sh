#!/bin/bash
set -e  # エラーが発生したら即座に終了

# uvicornをバックグラウンドで実行
uvicorn app.main:app --host 0.0.0.0 --port 6302 &

# Chainlit で認証機能を使うには以下のコマンドを実行し.envファイルに書き込む必要あり
# chainlit create-secret コマンドを実行し、CHAINLIT_AUTH_SECRET を取得
SECRET_LINE=$(chainlit create-secret | grep '^CHAINLIT_AUTH_SECRET=')

# .envファイルが存在しない場合は作成
# [ -f .env ] || touch .env

# 一時ファイルを作成
TMP_FILE=$(mktemp)

# CHAINLIT_AUTH_SECRET の行を除外しながら.envファイルの内容をコピー
grep -v '^CHAINLIT_AUTH_SECRET=' .env > "$TMP_FILE" || true

# 新しい SECRET_LINE (CHAINLIT_AUTH_SECRET) を一時ファイルに追加
printf '\n' >> "$TMP_FILE"  # 改行を追加
echo "$SECRET_LINE" >> "$TMP_FILE"

# 一時ファイルを.envファイルに移動
mv "$TMP_FILE" .env

# 一時ファイルが残っている場合は削除
[ -f "$TMP_FILE" ] && rm "$TMP_FILE"

# コンテナ内に設定された環境変数に反映させるために、新しい.envファイルを読み込む
# source コマンドを実行するには bash が必要
source /app/.env

# chainlitをフォアグラウンドで実行
exec chainlit run app/chainlit/chainlit_app.py -w --host 0.0.0.0 --port 8491