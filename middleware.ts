import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';

export async function middleware(request: NextRequest) {
    // ユーザーの認証状態をサーバーサイドでチェックします。
    // 未認証の場合は /signin にリダイレクトします。
    // 認証済みの場合は指定された外部URLにリダイレクトします。
    const supabase = createClient();
    const user = await getUser(supabase);

    if (!user) {
        return NextResponse.redirect(new URL('/signin', request.url));
    }

    return NextResponse.redirect('https://d206-34-173-37-132.ngrok-free.app/');
}

// matcher 設定により、/chainlit 以下の全てのパスに対してミドルウェアが適用されます
export const config = {
    matcher: '/chainlit/:path*',
};