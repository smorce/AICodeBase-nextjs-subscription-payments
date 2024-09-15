import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';

export async function middleware(request: NextRequest) {
    // ユーザーの認証状態をサーバーサイドでチェックします。
    // 未認証の場合は /signin にリダイレクトします。
    // 認証済みの場合はアクセストークンを含めて外部URLにリダイレクトします。
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

    // アクセストークンをURLに含めてリダイレクト
    const redirectUrl = new URL('https://d206-34-173-37-132.ngrok-free.app/');
    redirectUrl.searchParams.set('access_token', session.access_token);

    return NextResponse.redirect(redirectUrl);
}

// matcher 設定により、/chainlit 以下の全てのパスに対してミドルウェアが適用されます
export const config = {
    matcher: '/chainlit/:path*',
};