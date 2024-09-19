// これはサーバーサイドにすること
// 'use client'; は使わずに Page2Content の方に分離して、そっちでクライアントサイドを実装すること
import { redirect } from 'next/navigation';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';
import Page2Content from './Page2Content';

export default async function Page2() {
    const supabase = createClient();
    const user = await getUser(supabase);

    if (!user) {
      return redirect('/signin');
    }

    return <Page2Content />;
}