import { redirect } from 'next/navigation';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';
import { Playground } from './playground'; // Playgroundコンポーネントをインポート
import { ChainlitAPI } from "@chainlit/react-client";
import Page3Client from './Page3Client'; // 新しいクライアントコンポーネントをインポート

// ★ 「/chainlit」 はいる？？
 // まだバックエンドとフロントエンドの分離をしていないので chainlit は一旦 Colab で動かしている。
const CHAINLIT_SERVER = "https://d206-34-173-37-132.ngrok-free.app/chainlit"; // ChainlitサーバーのURLを適宜変更

export default async function Page3() {
  const supabase = createClient();
  const user = await getUser(supabase);

  if (!user) {
    return redirect('/signin');
  }

  const apiClient = new ChainlitAPI(CHAINLIT_SERVER, "webapp");

  return (
    <Page3Client apiClient={apiClient}>
      <main className="p-4">
        <h1 className="text-2xl font-bold">ページ3</h1>
        <Playground /> {/* 動的にインポートされた Playground コンポーネント */}
      </main>
    </Page3Client>
  );
}