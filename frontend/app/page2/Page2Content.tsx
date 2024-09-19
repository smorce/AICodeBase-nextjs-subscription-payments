'use client'

import { useState } from 'react';

export default function Page2Content() {
    const [message, setMessage] = useState('');
    const [tableData, setTableData] = useState<any[]>([]);

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

    const handleDeleteTable = async () => {
        try {
            const res = await fetch('http://localhost:6302/delete_table', {
                method: 'POST',
            });
            const data = await res.json();
            setMessage(data.message);
        } catch (error) {
            setMessage('テーブル削除に失敗しました');
            console.error(error);
        }
    };

    const handleReadTable = async () => {
        try {
            const res = await fetch('http://localhost:6302/read_table', {
                method: 'GET',
            });
            const data = await res.json();
            if (data.items) {
                setTableData(data.items);
                setMessage('テーブルの内容を取得しました');
            } else {
                setMessage(data.message);
            }
        } catch (error) {
            setMessage('テーブルの読み取りに失敗しました');
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
                        className="px-4 py-2 bg-red-500 text-white rounded mr-2"
                    >
                        DB削除
                    </button>
                    <button
                        onClick={handleDeleteTable}
                        className="px-4 py-2 bg-yellow-500 text-white rounded mr-2"
                    >
                        テーブル削除
                    </button>
                    <button
                        onClick={handleReadTable}
                        className="px-4 py-2 bg-green-500 text-white rounded"
                    >
                        テーブル内容確認
                    </button>
                </div>
                {message && <p className="mt-2 text-green-600">{message}</p>}
                {/* テーブルデータの表示 */}
                {tableData.length > 0 && (
                    <div className="mt-4">
                        <h2 className="text-xl font-semibold">テーブル内容:</h2>
                        <table className="min-w-full mt-2 border">
                            <thead>
                                <tr>
                                    <th className="border px-4 py-2">ID</th>
                                    <th className="border px-4 py-2">名前</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tableData.map((item) => (
                                    <tr key={item.id}>
                                        <td className="border px-4 py-2">{item.id}</td>
                                        <td className="border px-4 py-2">{item.name}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
                {/* ブランクページのコンテンツ */}
            </main>
        </>
    );
}