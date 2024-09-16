## Next.jsとFastAPIを用いた簡易Webアプリケーション構築 - ユーザー認証とSQLite連携

### 概要

このドキュメントでは、Next.js (フロントエンド) と FastAPI (バックエンド) を使用して構築した簡易的なWebアプリケーションについて説明します。このアプリケーションは、JWTによるユーザー認証、SQLiteデータベースとの連携、CORS設定などの基本的な機能を備えています。

### 技術スタック

* **フロントエンド:** Next.js
* **バックエンド:** FastAPI
* **データベース:** SQLite
* **認証:** JWT (JSON Web Token)
* **その他:**
    * passlib (パスワードハッシュ化)
    * jose (JWT)

### 機能

* ユーザー登録
* ユーザーログイン
* 認証によるAPIアクセス制御
* データベースの作成と削除
* サンプルデータ (アイテム) の追加、変更、削除
* ユーザーアカウントの削除
* CORS設定

### ディレクトリ構成

```
project/
├── backend/
│   ├── api/
│   │   ├── routes.py
│   │   ├── dependencies.py
│   │   └── __init__.py
│   ├── models/
│   │   ├── models.py
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── schemas.py
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py
│   │   └── __init__.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── pages/
    │   ├── page2/
    │   │   └── page.tsx
    │   ├── login/
    │   │   └── page.tsx
    │   └── _app.tsx
    ├── next.config.js
    ├── package.json
    └── ...
```

### 実装の詳細

#### バックエンド (FastAPI)

* **main.py:**
    * FastAPIアプリケーションの初期化とCORSミドルウェアの設定を行います。
* **api/routes.py:**
    * APIエンドポイントの定義を行います。
    * ユーザー登録 (`/register`)、ログイン (`/token`)、アイテム操作 (`/items/`), データベース操作 (`/create-db`, `/delete-db`), アカウント削除 (`/delete-account`) などのエンドポイントがあります。
    * 認証が必要なエンドポイントには `Depends(get_current_user)` を使用してアクセス制御を行います。
* **api/dependencies.py:**
    * データベースセッションの取得 (`get_db`) とユーザー認証 (`get_current_user`) などの依存関係を定義します。
    * `get_current_user` ではJWTトークンを検証し、ユーザー情報を取得します。
* **models/models.py:**
    * データベースモデル (`Item`, `User`) を定義します。
    * passlib を使用してパスワードをハッシュ化します。
* **schemas/schemas.py:**
    * APIリクエストとレスポンスのスキーマ (`ItemBase`, `ItemCreate`, `Item`, `UserCreate`, `User`, `Token`, `TokenData`) を定義します。
* **core/config.py:**
    * アプリケーションの設定 (プロジェクト名、データベースURL、JWTシークレットキー) を管理します。
    * `.env` ファイルから環境変数を読み込みます。

#### フロントエンド (Next.js)

* **page2/page.tsx:**
    * データベース操作とユーザー操作を行うためのUIを提供します。
    * 各ボタンは対応するAPIエンドポイントを呼び出します。
    * ログイン状態を確認し、未ログインの場合はログインページ (`/login`) にリダイレクトします。
* **login/page.tsx:**
    * ユーザーログインのためのフォームを提供します。
    * `/api/token` エンドポイントにログインリクエストを送信し、JWTトークンを取得します。
    * 取得したトークンは `localStorage` に保存します。
* **next.config.js:**
    * APIリクエストをバックエンドにプロキシするための設定を行います。


### 実行方法

1. バックエンドとフロントエンドの両方のプロジェクトで必要なパッケージをインストールします。
    * バックエンド: `pip install -r requirements.txt`
    * フロントエンド: `npm install`
2. `.env` ファイルに `JWT_SECRET_KEY` を設定します。
3. バックエンドとフロントエンドをそれぞれ起動します。
    * バックエンド: `uvicorn app.main:app --reload`
    * フロントエンド: `npm run dev`
4. ブラウザでフロントエンドアプリケーションにアクセスします (例: `http://localhost:3000`)。

#### JWT_SECRET_KEY の設定方法

セキュアな JWT_SECRET_KEY を生成するには、Pythonの secrets モジュールを使用します。以下のスクリプトを実行してキーを生成してください。
```python
import secrets

secret_key = secrets.token_urlsafe(32)
print(secret_key)
```

このスクリプトを実行すると、ランダムな32バイトのURLセーフなキーが生成されます。

.env ファイルへの追加:
生成した JWT_SECRET_KEY をプロジェクトの .env ファイルに追加します。
```plaintext
PROJECT_NAME="AI Subscription Payments"
DATABASE_URL="sqlite:///./test.db"
JWT_SECRET_KEY="your-secure-secret-key"
```

### 今後の課題

* ユーザー管理機能の強化 (ユーザー情報編集、パスワード変更など)
* 決済機能の実装 (Stripeなどの決済サービスとの連携)
* テストの拡充
* デプロイの自動化
* セキュリティ対策の強化

### まとめ

このドキュメントでは、Next.jsとFastAPIを用いて構築した簡易Webアプリケーションについて説明しました。このアプリケーションは、JWT認証とSQLiteデータベース連携の基本的な機能を備えており、今後の開発の基盤として活用できます。