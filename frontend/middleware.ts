// @supabase/auth-helpers-nextjs は古い。今は @supabase/ssr パッケージを使用する
// ----------------------------------
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { createServerClient, type CookieOptions } from '@supabase/ssr';

export async function middleware(request: NextRequest) {
    let response = NextResponse.next({
        request: {
            headers: request.headers,
        },
    });

    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                get(name: string) {
                    return request.cookies.get(name)?.value;
                },
                set(name: string, value: string, options: CookieOptions) {
                    response.cookies.set({
                        name,
                        value,
                        ...options,
                    });
                },
                remove(name: string, options: CookieOptions) {
                    response.cookies.set({
                        name,
                        value: '',
                        ...options,
                    });
                },
            },
            // Supabaseクライアントは自動的にトークンを更新し、セッションを維持する
            auth: {
                autoRefreshToken: true,
                persistSession: true
            }
        }
    );

    // セッションの更新を試みる（必要な場合）
    await supabase.auth.getSession();
    
    // ユーザーの認証状態を確認
    const {
        data: { user },
    } = await supabase.auth.getUser();

    // 認証されていない場合、サインインページにリダイレクト
    if (!user && !request.nextUrl.pathname.startsWith('/signin')) {
        return NextResponse.redirect(new URL('/signin', request.url));
    }

    // 認証されている場合、/chainlit へのアクセスを http://127.0.0.1:8491/ にリダイレクト
    if (user && request.nextUrl.pathname.startsWith('/chainlit')) {
        const redirectUrl = new URL('http://127.0.0.1:8491/');
        return NextResponse.redirect(redirectUrl);
    }
    
    // 認証されている場合、/langgraph へのアクセスを http://127.0.0.1:8492/ にリダイレクト
    if (user && request.nextUrl.pathname.startsWith('/langgraph')) {
        const redirectUrl = new URL('http://127.0.0.1:8492/');
        return NextResponse.redirect(redirectUrl);
    }

    // 認証されている場合、/callbacks へのアクセスを http://127.0.0.1:8493/ にリダイレクト
    if (user && request.nextUrl.pathname.startsWith('/callbacks')) {
        const redirectUrl = new URL('http://127.0.0.1:8493/');
        return NextResponse.redirect(redirectUrl);
    }

    // 認証されている場合、/auto_documentor へのアクセスを http://127.0.0.1:8494/ にリダイレクト
    if (user && request.nextUrl.pathname.startsWith('/auto_documentor')) {
        const redirectUrl = new URL('http://127.0.0.1:8494/');
        return NextResponse.redirect(redirectUrl);
    }

    return response;
}

// matcher 設定により、/chainlit, /langgraph, /callbacks, auto_documentor 以下の全てのパスに対してミドルウェアが適用されます
export const config = {
    matcher: ['/chainlit/:path*', '/langgraph/:path*', '/callbacks/:path*', '/auto_documentor/:path*'],
};