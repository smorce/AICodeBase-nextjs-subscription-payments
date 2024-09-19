'use client'

import { useState } from 'react';

export default function Page2Content() {
    const [message, setMessage] = useState('');

    const handleCreateDB = async () => {
        try {
            const res = await fetch('http://localhost:6302/create_db', {
                method: 'POST',
            });
            const data = await res.json();
            setMessage(data.message);
        } catch (error) {
            setMessage('DB作成に失敗しました');
            console.error(error);
        }
    };

    const handleDeleteDB = async () => {
        try {
            const res = await fetch('http://localhost:6302/delete_db', {
                method: 'POST',
            });
            const data = await res.json();
            setMessage(data.message);
        } catch (error) {
            setMessage('DB削除に失敗しました');
            console.error(error);
        }
    };

    return (
        <>
            <main className="p-4">
                <h1 className="text-2xl font-bold">ページ2</h1>
                {/* DB作成・削除ボタン */}
                <div className="mt-4">
                    <button
                        onClick={handleCreateDB}
                        className="px-4 py-2 bg-blue-500 text-white rounded mr-2"
                    >
                        DB作成
                    </button>
                    <button
                        onClick={handleDeleteDB}
                        className="px-4 py-2 bg-red-500 text-white rounded"
                    >
                        DB削除
                    </button>
                </div>
                {message && <p className="mt-2 text-green-600">{message}</p>}
                {/* ブランクページのコンテンツ */}
            </main>
        </>
    );
}