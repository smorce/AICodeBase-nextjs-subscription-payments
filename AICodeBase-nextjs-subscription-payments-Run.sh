#!/bin/bash

# 初回実行は実行権限をつける
# chmod +x AICodeBase-nextjs-subscription-payments-Run.sh

# プロジェクト名を小文字に
PROJECT_NAME="aicodebasse"

# docker-compose.ymlファイルのパスを設定
COMPOSE_FILE="compose.yaml"

# Dockerfileのハッシュを計算
DOCKERFILE="Dockerfile"
dockerfile_hash=$(md5sum $DOCKERFILE | awk '{print $1}')

# docker-compose.ymlからサービス名を取得
services=$(docker compose -f $COMPOSE_FILE config --services)

# イメージが存在するか確認する関数
check_images() {
    local check_type=$1
    for service in $services; do
        local image_name=$(docker compose -f $COMPOSE_FILE config | grep -A 1 "services:" | grep "$service:" -A 3 | grep "image:" | awk '{print $2}')
        if [[ -z "$image_name" ]]; then
            image_name="${PROJECT_NAME}_${service}"
        fi
        if [[ $check_type == "latest" ]]; then
            if [[ "$(docker images -q ${image_name}:latest 2> /dev/null)" == "" ]]; then
                return 1
            fi
        elif [[ $check_type == "hash" ]]; then
            if [[ "$(docker images -q ${image_name}:$dockerfile_hash 2> /dev/null)" == "" ]]; then
                return 1
            fi
        fi
    done
    return 0
}

# イメージが存在しないか確認
if ! check_images "latest"; then
    echo "一つ以上のサービスのイメージが存在しないため、新規ビルドを行います。"
    docker compose -f $COMPOSE_FILE up --build -d
elif ! check_images "hash"; then
    echo "Dockerfileに変更があるため、再ビルドを行います。"
    # 古いイメージを削除
    for service in $services; do
        local image_name=$(docker compose -f $COMPOSE_FILE config | grep -A 1 "services:" | grep "$service:" -A 3 | grep "image:" | awk '{print $2}')
        if [[ -z "$image_name" ]]; then
            image_name="${PROJECT_NAME}_${service}"
        fi
        docker rmi ${image_name}:latest
    done
    # 新しいイメージをビルド
    docker compose -f $COMPOSE_FILE up --build -d
    # 新しいイメージにハッシュタグを追加
    for service in $services; do
        local image_name=$(docker compose -f $COMPOSE_FILE config | grep -A 1 "services:" | grep "$service:" -A 3 | grep "image:" | awk '{print $2}')
        if [[ -z "$image_name" ]]; then
            image_name="${PROJECT_NAME}_${service}"
        fi
        docker tag ${image_name}:latest ${image_name}:$dockerfile_hash
    done
else
    echo "イメージは最新です。既存のコンテナを起動します。"
    docker compose -f $COMPOSE_FILE up -d
fi

echo "コンテナが起動しました。ログを表示します："
docker compose -f $COMPOSE_FILE logs -f