// Supabase のログイン機能を削除
// import { redirect } from 'next/navigation';
// import { createClient } from '@/utils/supabase/server';
// import { getUser } from '@/utils/supabase/queries';

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';

// Supabase のログイン機能を削除したため、非同期関数から同期関数に変更
// export default async function Page2() {
export default function Page2() {
    const router = useRouter();
    const [message, setMessage] = useState('');

    // SQLite でユーザーとアイテム情報を管理
    useEffect(() => {
        const checkUser = async () => {
            const token = localStorage.getItem('access_token');
            if (!token) {
                router.push('/login');
            }
        };
        checkUser();
    }, [router]);

    const getToken = () => {
        return localStorage.getItem('access_token');
    };

    const handleCreateDB = async () => {
        try {
            const response = await fetch('/api/create-db', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                },
            });
            const data = await response.json();
            setMessage(data.message);
        } catch (error) {
            setMessage('DB作成に失敗しました。');
        }
    };

    const handleAddSampleData = async () => {
        try {
            const response = await fetch('/api/items/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getToken()}`,
                },
                body: JSON.stringify({ name: 'サンプルアイテム', description: 'これはサンプルデータです。' }),
            });
            const data = await response.json();
            setMessage(`アイテムが追加されました: ID ${data.id}`);
        } catch (error) {
            setMessage('サンプルデータの追加に失敗しました。');
        }
    };

    const handleUpdateSampleData = async () => {
        try {
            const response = await fetch('/api/items/1', { // ID 1 のアイテムを更新
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getToken()}`,
                },
                body: JSON.stringify({ name: '更新されたアイテム', description: 'データが更新されました。' }),
            });
            const data = await response.json();
            setMessage(`アイテムが更新されました: ID ${data.id}`);
        } catch (error) {
            setMessage('サンプルデータの更新に失敗しました。');
        }
    };

    const handleDeleteSampleData = async () => {
        try {
            const response = await fetch('/api/items/1', { // ID 1 のアイテムを削除
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                },
            });
            const data = await response.json();
            setMessage(`アイテムが削除されました: ${data.detail}`);
        } catch (error) {
            setMessage('サンプルデータの削除に失敗しました。');
        }
    };

    const handleDeleteDB = async () => {
        try {
            const response = await fetch('/api/delete-db', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                },
            });
            const data = await response.json();
            setMessage(data.message);
        } catch (error) {
            setMessage('DB削除に失敗しました。');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        setMessage('ログアウトしました。');
        router.push('/login');
    };

    const handleDeleteAccount = async () => {
        try {
            const response = await fetch('/api/delete-account', {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                },
            });
            const data = await response.json();
            setMessage(data.message);
            handleLogout();
        } catch (error) {
            setMessage('アカウント削除に失敗しました。');
        }
    };

    return (
        <>
            <main className="p-4">
                <h1 className="text-2xl font-bold">ページ2</h1>
                <div className="mt-4 space-y-2">
                    <button onClick={handleCreateDB} className="px-4 py-2 bg-blue-500 text-white rounded">
                        DBの作成
                    </button>
                    <button onClick={handleAddSampleData} className="px-4 py-2 bg-green-500 text-white rounded">
                        サンプルデータの追加
                    </button>
                    <button onClick={handleUpdateSampleData} className="px-4 py-2 bg-yellow-500 text-white rounded">
                        サンプルデータの変更
                    </button>
                    <button onClick={handleDeleteSampleData} className="px-4 py-2 bg-red-500 text-white rounded">
                        サンプルデータの削除
                    </button>
                    <button onClick={handleDeleteDB} className="px-4 py-2 bg-gray-500 text-white rounded">
                        DBの削除
                    </button>
                    <button onClick={handleLogout} className="px-4 py-2 bg-red-700 text-white rounded">
                        ログアウト
                    </button>
                    <button onClick={handleDeleteAccount} className="px-4 py-2 bg-purple-500 text-white rounded">
                        アカウント削除
                    </button>
                </div>
                {message && <p className="mt-4 text-center text-lg">{message}</p>}
            </main>
        </>
    );
}