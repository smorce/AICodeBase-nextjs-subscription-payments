### プロジェクト概要
このプロジェクトは、Next.js、Supabase、Stripe、Drizzle、Tailwind CSSを使用する新しいWebアプリケーションのための出発点として機能することを目的としています。これは、ユーザー認証、決済処理、サブスクリプション管理、CRUD（作成、読み取り、更新、削除）操作を実行するためのサンプルコードと構成を提供するボイラープレートプロジェクトです。

### プロジェクトの構成
```Directory Structure
AICodeBase/
├── actions
│   ├── favicon.ico
│   └── stripe-actions.ts
├── app
│   ├── (auth)
│   │   ├── layout.tsx
│   │   ├── login
│   │   │   └── page.tsx
│   │   └── signup
│   │       └── page.tsx
│   ├── api
│   │   └── stripe
│   │       └── webhooks
│   │           └── route.ts
│   ├── favicon.ico
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── backend
├── db
│   ├── db.ts
│   ├── migrations
│   │   └── 0000_XXXXX.sql
│   ├── queries
│   │   └── example-queries.ts
│   └── schema
│       ├── example-schema.ts
│       └── index.ts
├── .env.local
├── .gitignore
├── components
│   ├── utilities
│   │   └── providers.tsx
│   └── header.tsx
├── drizzle.config.ts
├── lib
│   └── stripe.ts
├── next.config.mjs
├── next-env.d.ts
├── node_modules
├── package.json
├── package-lock.json
├── postcss.config.mjs
├── prompts
│   ├── setup-backend.md
│   ├── setup-frontend.md
│   ├── setup-payments.md
│   ├── setup-project.md
│   └── setup-supabase-auth.md
├── public
│   ├── next.svg
│   └── vercel.svg
├── README.md
├── tailwind.config.ts
├── tsconfig.json
├── types
│   ├── action-types.ts
│   └── index.ts
└── utils
    └── supabaseClient.ts
```

- `actions/example-actions.ts`
```plaintext
このコードは、Next.jsのサーバーコンポーネントで実行されるであろう、Example データを管理するための一連のアクションを定義しています。各アクションは、データベースとのやり取りを行い、Example の作成、取得、更新、削除といった操作を実行します。アクションは非同期で実行され、成功または失敗を示す ActionState オブジェクトを返します。また、必要に応じて Next.js の revalidatePath 関数を使用して、関連するページのキャッシュを無効化し、再検証をトリガーします。
```

- `actions/stripe-actions.ts`
```plaintext
このコードは、Stripeのサブスクリプションイベントを処理するためのアクションを定義しています。具体的には、ユーザーのStripe顧客情報を更新する updateStripeCustomer 関数と、サブスクリプションのステータス変更を管理する manageSubscriptionStatusChange 関数が含まれています。

- getMembershipStatus: Stripeのサブスクリプションステータスに基づいて、ユーザーのメンバーシップステータスを決定する関数。
- updateStripeCustomer: ユーザーのプロフィールを更新し、Stripeの顧客IDとサブスクリプションIDを保存します。
  - profileId: ユーザーのプロフィールID。
  - subscriptionId: StripeのサブスクリプションID。
  - customerId: Stripeの顧客ID。
- manageSubscriptionStatusChange: サブスクリプションのステータス変更に基づいて、ユーザーのメンバーシップステータスを更新します。
  - subscriptionId: StripeのサブスクリプションID。
  - customerId: Stripeの顧客ID。
  - productId: Stripeの製品ID。
```

- `app/(auth)/layout.tsx`
```plaintext
このコードは、認証関連のページ（ログイン、サインアップなど）で使用するレイアウトコンポーネント AuthLayout を定義しています。コンテンツを常に画面の中央に表示しています。
```

- `app/(auth)/login/page.tsx`
```plaintext
このコードは、Supabaseを用いたログインページを実装しています。Googleによるログインをサポートしています。ユーザーがGoogleアカウントでログインすると、Supabaseが認証を処理し、ユーザーセッションが作成されます。
```

- `app/(auth)/signup/page.tsx`
```plaintext
このコードは、Supabaseを用いたサインアップページを実装しています。Googleによるサインアップをサポートしています。ユーザーがGoogleアカウントでサインアップすると、Supabaseが認証を処理し、新しいユーザーアカウントとユーザーセッションが作成されます。
```

- `app/(auth)/signup/page.tsx`
```plaintext
このコードは、Supabaseを用いたサインアップページを実装しています。ユーザーはメールアドレスとパスワードを使用して新しいアカウントを作成することができます。
```

- `app/page.tsx`
```plaintext
このコードは、Next.jsアプリケーションのホーム画面のコンポーネントを定義しています。このコンポーネントは、ユーザーが認証されている場合、ユーザーがデータベース内の"example"エンティティを作成、読み取り、更新、削除するためのインターフェースを提供します。ユーザーはフォームを使用して新しいエンティティを作成し、IDで既存のエンティティを取得し、既存のエンティティを更新し、IDでエンティティを削除することができます。各アクションの結果は、ページに表示されます。認証されていない場合は、ログインページにリダイレクトします。
```

- `app/layout.tsx`
```plaintext
このコードは、Next.js アプリケーションのルートレイアウトを定義しています。アプリケーション全体の共通レイアウト、フォント、スタイル、コンテキストプロバイダーなどを設定し、Supabaseのセッション情報をアプリケーション全体で利用できるようにしています。

- metadata: アプリケーションのメタデータを定義 (タイトル、説明など)
- RootLayout: アプリケーションのルートレイアウトコンポーネント。
- SessionContextProvider: Supabaseのセッション情報をアプリケーション全体で利用できるようにするコンテキストプロバイダー。
- supabaseClient: Supabaseクライアントインスタンス。
- Providers: Shadcn/ui のテーマやコンテキストを提供するコンポーネントをラップしています。
- Toaster: Shadcn/ui のトースト通知を表示するためのコンポーネント。
- children: 各ページのコンテンツがここにレンダリングされます。
- inter: Google Fonts の Inter フォントを読み込んで適用しています。
- globals.css: アプリケーション全体のグローバルスタイルをインポートしています。
```

- `app/api/stripe/webhooks/route.ts`
```plaintext
このコードは、Stripe webhook イベントを処理するための Next.js API ルートを定義しています。Stripe から送信されたイベントを検証し、関連するイベント（サブスクリプションの更新、削除、チェックアウトセッションの完了）に応じて適切なアクションを実行します。

- relevantEvents: 処理対象の Stripe イベントタイプを定義した Set。
- イベントタイプに応じて以下のアクションを実行します。
  - customer.subscription.updated / customer.subscription.deleted: manageSubscriptionStatusChange 関数を呼び出し、サブスクリプションのステータス変更を処理します。
  - checkout.session.completed: updateStripeCustomer 関数を呼び出し、顧客情報を更新し、manageSubscriptionStatusChange 関数を呼び出してサブスクリプションのステータス変更を処理します。
- エラー発生時はエラーメッセージを返します。
- 正常終了時は "received: true" を含む JSON レスポンスを返します。
```

- `components/header.tsx`
```plaintext
このコードは、アプリケーションのヘッダーコンポーネントを定義しています。ヘッダーには、ユーザーの認証状態に応じてログイン/サインアップボタンまたはログアウトボタンとユーザーのメールアドレスが表示されます。
```

- `components/utilities/providers.tsx`
```plaintext
このコードは、アプリケーション全体で利用されるコンテキストプロバイダーをまとめて管理するコンポーネント Providers を定義しています。具体的には、テーマの切り替えとツールチップの表示に関するプロバイダーを提供しています。

- Providers: 複数のプロバイダーをまとめて管理するコンポーネント。
- NextThemesProvider: next-themes ライブラリを利用して、ダークモードとライトモードの切り替え機能を提供します。
- TooltipProvider: Tooltip コンポーネントを利用するためのコンテキストを提供します。
- children: Providers コンポーネントでラップされた子コンポーネントは、これらのプロバイダーが提供する機能を利用できます。
```

- `db/migrations/0000_XXXXX.sql`
```plaintext
このコードは、SQLを使用して "example" という名前のテーブルを作成するデータベースマイグレーションスクリプトです。このテーブルは、ユーザーなどのエンティティの基本的な情報を格納するように設計されています。

- id: UUID型の主キーで、デフォルトでランダムなUUIDが生成されます。
- name: テキスト型の必須フィールドで、おそらくエンティティの名前を格納します。
- age: 整数型の必須フィールドで、エンティティの年齢を表します。
- email: テキスト型の必須フィールドで、エンティティのメールアドレスを格納します。
- created_at: タイムスタンプ型の必須フィールドで、エンティティの作成日時を記録し、デフォルトで現在のタイムスタンプが設定されます。
- updated_at: タイムスタンプ型の必須フィールドで、エンティティの最終更新日時を記録し、デフォルトで現在のタイムスタンプが設定されます。
```

- `db/queries/example-queries.ts`
```plaintext
このコードは、exampleTableというテーブルに対するCRUD操作（作成、読み取り、更新、削除）を行うためのデータベースクエリ関数を定義しています。Drizzle ORMを使用して、PostgreSQLデータベースと対話します。

- createExample: 新しいexampleレコードをデータベースに挿入します。
- getExampleById: IDに基づいてexampleレコードを取得します。
- getAllExamples: データベースからすべてのexampleレコードを取得します。
- updateExample: 既存のexampleレコードを更新します。
- deleteExample: IDに基づいてexampleレコードを削除します。
```

- `db/schema/example-schema.ts`
```plaintext
このコードは、TypeScriptで記述されたデータベーススキーマ定義の一部です。具体的には、"example" という名前のPostgreSQLテーブルのスキーマを定義しています。 drizzle-orm というORMライブラリを使用して、テーブルの構造（カラム名、データ型、制約など）を宣言的に定義しています。
```

- `db/schema/index.ts`
```plaintext
このコードは、db/schema/example-schema.ts から全てのエクスポートを再エクスポートするだけのインデックスファイルです。これにより、他のファイルから db/schema ディレクトリ全体をインポートする際に、`index.ts` ファイルを介して全てのスキーマにアクセスできるようになります。
```

- `db/db.ts`
```plaintext
このコードは、Drizzle ORM を使用して PostgreSQL データベースに接続するための設定を行っています。環境変数からデータベースの URL を読み込み、データベースクライアントを初期化し、スキーマを定義して Drizzle ORM のインスタンスを作成しています。
```

- `lib/stripe.ts`
```plaintext
このコードは、Stripe API を利用するための Stripe クライアントを初期化しています。Stripe のシークレットキーと API バージョン、アプリケーション情報を設定しています。

- stripe: Stripe クラスのインスタンス。Stripe API とのやり取りに利用されます。
- process.env.STRIPE_SECRET_KEY!: 環境変数から Stripe のシークレットキーを取得しています。! は値が必ず存在することをコンパイラに保証しています。
- apiVersion: 利用する Stripe API のバージョンを指定しています。
- appInfo: アプリケーションの名前とバージョンを指定しています。
```

- `types/action-types.ts`
```plaintext
このコードは、TypeScriptの型定義ファイルです。ActionStateという型を定義しており、これはアクションの状態を表すために使用されます。

- ActionState: アクションの状態を表す型。
  - status: アクションの状態を表す文字列で、"success"または"error"のいずれかです。
  - message: アクションの状態に関するメッセージです。
  - data: アクションに関連するデータ（任意）。
```

- `types/index.ts`
```plaintext
このコードは、`action-types` モジュールからエクスポートされたすべての要素を再エクスポートするだけのインデックスファイルです。
```

- `drizzle.config.ts`
```plaintext
このコードは、Drizzle ORMを使ったデータベースマイグレーションの設定ファイルです。 .env.local ファイルから環境変数を読み込み、PostgreSQL データベースへの接続情報とスキーマ定義ファイルの場所、マイグレーションファイルの出力先を指定しています。
```

- `utils/supabaseClient.ts`
```plaintext
このコードは、Supabaseクライアントを初期化し、エクスポートしています。

- supabaseUrl: SupabaseプロジェクトのURL。環境変数NEXT_PUBLIC_SUPABASE_URLから取得されます。
- supabaseAnonKey: Supabaseプロジェクトの匿名キー。環境変数NEXT_PUBLIC_SUPABASE_ANON_KEYから取得されます。
- supabase: createClient関数を使用して初期化されたSupabaseクライアント。データベースへのクエリや認証などの操作に使用できます。
```






