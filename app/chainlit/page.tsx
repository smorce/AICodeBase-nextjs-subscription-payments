import { redirect } from 'next/navigation';
import { createClient } from '@/utils/supabase/server';
import { getUser } from '@/utils/supabase/queries';

export default async function ChainlitPage() {
    const supabase = createClient();
    const user = await getUser(supabase);

    if (!user) {
        return redirect('/signin');
    }

    // ユーザーが存在する場合、指定されたURLにリダイレクト
    return redirect('https://d206-34-173-37-132.ngrok-free.app/');
}