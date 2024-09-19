FROM python:3.12.3-slim

# ビルド時の引数を定義
ARG UID=1002
ARG GID=1002

# ユーザーとグループを作成
RUN addgroup --gid $GID appgroup && \
    adduser --disabled-password --gecos "" --uid $UID --gid $GID appuser

WORKDIR /app

COPY ./app /app/app
COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# デフォルトユーザーを設定
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "6302"]