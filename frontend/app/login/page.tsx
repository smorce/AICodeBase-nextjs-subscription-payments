'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
    const router = useRouter();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');

    const handleLogin = async () => {
        try {
            const response = await fetch('http://backend:6302/api/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username,
                    password,
                }),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                setMessage('ログインに成功しました。');
                router.push('/page2');
            } else {
                const errorData = await response.json();
                setMessage(errorData.detail || 'ログインに失敗しました。');
            }
        } catch (error) {
            setMessage('ログイン中にエラーが発生しました。');
        }
    };

    return (
        <main className="p-4">
            <h1 className="text-2xl font-bold">ログイン</h1>
            <div className="mt-4">
                <label className="block">
                    ユーザー名:
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="border p-2 w-full"
                    />
                </label>
                <label className="block mt-2">
                    パスワード:
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="border p-2 w-full"
                    />
                </label>
                <button onClick={handleLogin} className="mt-4 px-4 py-2 bg-blue-500 text-white rounded">
                    ログイン
                </button>
                {message && <p className="mt-4 text-center text-lg">{message}</p>}
                {/* 新規登録へのリンクを追加 */}
                <p className="mt-4">
                    アカウントをお持ちでない場合は{' '}
                    <a href="/register" className="text-blue-500 underline">
                        こちら
                    </a>
                    から登録してください。
                </p>
            </div>
        </main>
    );
}