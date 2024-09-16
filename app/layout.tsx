import { Metadata } from 'next';
import Footer from '@/components/ui/Footer';
import Navbar from '@/components/ui/Navbar';
import { Toaster } from '@/components/ui/Toasts/toaster';
import { PropsWithChildren, Suspense } from 'react';
import { getURL } from '@/utils/helpers';
import 'styles/main.css';

const title = 'Next.js Subscription Starter';
const description = 'Brought to you by Vercel, Stripe, and Supabase.';

export const metadata: Metadata = {
  metadataBase: new URL(getURL()),
  title: title,
  description: description,
  openGraph: {
    title: title,
    description: description
  }
};


// 認証状態の確認:
// ユーザーの認証状態を確認し、ログイン/ログアウト状態に応じて適切なナビゲーション項目を表示するために、非同期処理をしている。

// 以下のエラーは一旦気にしない。
// Navbar' を JSX コンポーネントとして使用することはできません。
// 上記を修正するとしたら、
// Navbar コンポーネントを同期的なコンポーネントに変更し、データフェッチングを別のコンポーネント(NavlinksWrapper を作成する)に移動します。
// layout.tsx ファイルで Suspense を使用して、非同期コンポーネントをラップします。
// という方法になり、Navbar を使用している他のページでも、必要に応じて Suspense でラップすることになる。

export default async function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en">
      <body className="bg-black">
        <Navbar />
        <main
          id="skip"
          className="min-h-[calc(100dvh-4rem)] md:min-h[calc(100dvh-5rem)]"
        >
          {children}
        </main>
        <Footer />
        <Suspense>
          <Toaster />
        </Suspense>
      </body>
    </html>
  );
}