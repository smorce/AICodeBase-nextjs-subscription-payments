import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';

export async function middleware(request: NextRequest) {
    const supabase = createClient();
    const user = await getUser(supabase);

    if (!user) {
        return NextResponse.redirect(new URL('/signin', request.url));
    }

    return NextResponse.redirect('https://d206-34-173-37-132.ngrok-free.app/');
}

export const config = {
    matcher: '/chainlit/:path*',
};