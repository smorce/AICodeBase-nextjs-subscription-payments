import { redirect } from 'next/navigation';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';

export default async function Page2() {
    const supabase = createClient();
    const user = await getUser(supabase);

    if (!user) {
        return redirect('/signin');
    }

    return (
      <>
        <main className="p-4">
          <h1 className="text-2xl font-bold">ページ2</h1>
          {/* ブランクページのコンテンツ */}
        </main>
      </>
    );
}