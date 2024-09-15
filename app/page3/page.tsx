import { redirect } from 'next/navigation';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';
import Page3Client from './Page3Client'; // クライアントコンポーネントをインポート

export default async function Page3() {
  const supabase = createClient();
  const user = await getUser(supabase);

  if (!user) {
    return redirect('/signin');
  }

  return (
    <>
      <main className="p-4">
        <h1 className="text-2xl font-bold">ページ3</h1>
        {/* Playground コンポーネントをレンダリング */}
        <Page3Client />
      </main>
    </>
  );
}