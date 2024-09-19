'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function RegisterPage() {
    const router = useRouter();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [message, setMessage] = useState('');

    const handleRegister = async () => {
        try {
            const response = await fetch('http://backend:6302/api/register', { // 新規作成
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            if (response.ok) {
                const data = await response.json();
                setMessage('登録に成功しました。ログインしてください。');
                router.push('/login');
            } else {
                const errorData = await response.json();
                setMessage(errorData.detail || '登録に失敗しました。');
            }
        } catch (error) {
            setMessage('登録中にエラーが発生しました。');
        }
    };

    return (
        <main className="p-4">
            <h1 className="text-2xl font-bold">ユーザー登録</h1>
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
                <button onClick={handleRegister} className="mt-4 px-4 py-2 bg-green-500 text-white rounded">
                    登録
                </button>
                {message && <p className="mt-4 text-center text-lg">{message}</p>}
            </div>
        </main>
    );
}