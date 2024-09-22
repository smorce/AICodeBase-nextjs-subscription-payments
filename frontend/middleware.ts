// ■ セキュリティ向上案
// - トークンの有効期限管理:
// アクセストークンに有効期限を設定し、定期的にトークンを再発行する仕組みを導入すると、セキュリティがさらに強化されます。
// - クッキーの暗号化:
// 追加のセキュリティ層として、クッキーの内容を暗号化することを検討してください。
// これらの変更により、アクセストークンの管理がより安全になり、アプリケーション全体のセキュリティが向上します。他の関連ファイルに変更が必要な場合はお知らせください。
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';

export async function middleware(request: NextRequest) {
    // ユーザーの認証状態をサーバーサイドでチェックします。
    // 未認証の場合は /signin にリダイレクトします。
    // 認証済みの場合はアクセストークンをHTTP-onlyクッキーに設定し、外部URLにリダイレクトします。
    const supabase = createClient();
    const user = await getUser(supabase);

    if (!user) {
        return NextResponse.redirect(new URL('/signin', request.url));
    }

    // アクセストークンを取得
    const { data: { session } } = await supabase.auth.getSession();

    if (!session?.access_token) {
        return NextResponse.redirect(new URL('/signin', request.url));
    }

    // アクセストークンをURLに含めるのはセキュリティ上のリスクがあるため、代わりにHTTP-onlyクッキーを使用してアクセストークンを安全に管理するようにミドルウェアを修正
    // これにより、クライアントサイドのJavaScriptからアクセストークンにアクセスできなくなり、セキュリティが向上します。
    // response.cookies.set メソッドを使用して、アクセストークンをHTTP-onlyかつSecureなクッキーとして設定します。
        // sameSite: 'strict'を設定することで、CSRF攻撃に対する保護を強化します。
        // 本番環境 (process.env.NODE_ENV === 'production') の場合にのみ、secure属性をtrueに設定されます。これにより、HTTPS接続時のみクッキーが送信されます。開発中は HTTP 接続で OK。
        // path: '/'を指定することで、サイト全体でクッキーが有効になります。
    // アクセストークンをHTTP-onlyクッキーに設定
    const redirectUrl = new URL('http://127.0.0.1:8491/');
    const response = NextResponse.redirect(redirectUrl);
    response.cookies.set('access_token', session.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',     // Next.js では本番環境ではtrue、開発環境ではfalseに自動的になる
        sameSite: 'strict',
        path: '/',
    });

    return response;
}

// matcher 設定により、/chainlit 以下の全てのパスに対してミドルウェアが適用されます
export const config = {
    matcher: '/chainlit/:path*',
};