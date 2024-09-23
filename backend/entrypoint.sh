#!/bin/bash
set -e  # エラーが発生したら即座に終了

# root 権限で NTPsec を使って時刻を同期（バックグラウンドで実行）
ntpd -n &

# 非rootユーザーに切り替え
# 'appuser' ユーザーに切り替えて以下のコマンドを実行
exec su appuser -c "bash" << 'EOF'

# uvicornをバックグラウンドで実行
uvicorn app.main:app --host 0.0.0.0 --port 6302 &

# Chainlit で認証機能を使うには以下のコマンドを実行し.envファイルに書き込む必要あり
# chainlit create-secret コマンドを実行し、CHAINLIT_AUTH_SECRET を取得
SECRET_LINE=$(chainlit create-secret | grep '^CHAINLIT_AUTH_SECRET=')

# 一時ファイルを作成
TMP_FILE=$(mktemp)

# CHAINLIT_AUTH_SECRET の行を除外しながら.envファイルの内容をコピー
grep -v '^CHAINLIT_AUTH_SECRET=' .env > "$TMP_FILE" || true

# 新しい SECRET_LINE (CHAINLIT_AUTH_SECRET) を一時ファイルに追加
echo "$SECRET_LINE" >> "$TMP_FILE"  # 改行はechoが自動で追加します

# 各行の末尾の余分な空白を削除
sed -i 's/[[:space:]]*$//' "$TMP_FILE"

# 最後の空行を削除。実際に空行が残っているように見えるのは空行ではない可能性がある。一旦このままで。
sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$TMP_FILE"

# 一時ファイルを.envファイルに移動
mv "$TMP_FILE" .env

# 一時ファイルが残っている場合は削除
[ -f "$TMP_FILE" ] && rm "$TMP_FILE"

# コンテナ内に設定された環境変数に反映させるために、新しい.envファイルを読み込む
# source コマンドを実行するには bash が必要なので sh から変更した
source /app/.env

# chainlitをフォアグラウンドで実行（このタイミングで実行したあとに場所をCOPYで移動させているため、-w でリロードするとおかしくなる）
exec chainlit run app/chainlit/chainlit_app.py -w --host 0.0.0.0 --port 8491

EOF