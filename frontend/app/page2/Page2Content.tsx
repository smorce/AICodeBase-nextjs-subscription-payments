'use client'

import { useState } from 'react';

export default function Page2Content() {
    const [message, setMessage] = useState('');
    const [tableData, setTableData] = useState<any[]>([]);
    const [users, setUsers] = useState<any[]>([]);
    const [newUser, setNewUser] = useState({ name: '', password: '' });
    const [updateUser, setUpdateUser] = useState({ id: '', name: '', password: '' });
    const [deleteUserId, setDeleteUserId] = useState('');

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
            setTableData([]); // DB削除後にアイテムデータをクリア
            setUsers([]);     // DB削除後にユーザーデータをクリア
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
                // データベースからアイテムとユーザーの両方を取得した後、setUsers(data.users || []) を追加し、ユーザーデータをステートに設定しています。これにより、ユーザー一覧が最新のデータで表示されます
                setUsers(data.users || []);
                setMessage('テーブルの内容を取得しました');
            } else {
                setMessage(data.message);
            }
        } catch (error) {
            setMessage('テーブルの読み取りに失敗しました');
            console.error(error);
        }
    };

    const handleCreateUser = async () => {
        try {
            const res = await fetch('http://localhost:6302/users/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newUser),
            });
            const data = await res.json();
            if (res.ok) {
                setUsers([...users, data.user]);
                setMessage(data.message);
                setNewUser({ name: '', password: '' });
            } else {
                setMessage(data.detail || 'ユーザー作成に失敗しました');
            }
        } catch (error) {
            setMessage('ユーザー作成に失敗しました');
            console.error(error);
        }
    };

    const handleUpdateUser = async () => {
        try {
            const res = await fetch(`http://localhost:6302/users/${updateUser.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: updateUser.name || undefined,
                    password: updateUser.password || undefined,
                }),
            });
            const data = await res.json();
            if (res.ok) {
                setUsers(users.map(user => user.id === data.user.id ? data.user : user));
                setMessage(data.message);
                setUpdateUser({ id: '', name: '', password: '' });
            } else {
                setMessage(data.detail || 'ユーザー更新に失敗しました');
            }
        } catch (error) {
            setMessage('ユーザー更新に失敗しました');
            console.error(error);
        }
    };

    const handleDeleteUser = async () => {
        try {
            const res = await fetch(`http://localhost:6302/users/${deleteUserId}`, {
                method: 'DELETE',
            });
            const data = await res.json();
            if (res.ok) {
                setUsers(users.filter(user => user.id !== parseInt(deleteUserId)));
                setMessage(data.message);
                setDeleteUserId('');
            } else {
                setMessage(data.detail || 'ユーザー削除に失敗しました');
            }
        } catch (error) {
            setMessage('ユーザー削除に失敗しました');
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
                
                {/* アイテムデータの表示 */}
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

                {/* ユーザー管理セクション */}
                <div className="mt-8">
                    <h2 className="text-2xl font-bold">ユーザー管理</h2>
                    
                    {/* ユーザー作成フォーム */}
                    <div className="mt-4 p-4 border rounded">
                        <h3 className="text-xl font-semibold">ユーザー作成</h3>
                        <input
                            type="text"
                            placeholder="名前"
                            value={newUser.name}
                            onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                            className="mt-2 p-2 border rounded w-full"
                        />
                        <input
                            type="password"
                            placeholder="パスワード"
                            value={newUser.password}
                            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                            className="mt-2 p-2 border rounded w-full"
                        />
                        <button
                            onClick={handleCreateUser}
                            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
                        >
                            ユーザー作成
                        </button>
                    </div>

                    {/* ユーザー更新フォーム */}
                    <div className="mt-4 p-4 border rounded">
                        <h3 className="text-xl font-semibold">ユーザー更新</h3>
                        <input
                            type="number"
                            placeholder="ユーザーID"
                            value={updateUser.id}
                            onChange={(e) => setUpdateUser({ ...updateUser, id: e.target.value })}
                            className="mt-2 p-2 border rounded w-full"
                        />
                        <input
                            type="text"
                            placeholder="新しい名前"
                            value={updateUser.name}
                            onChange={(e) => setUpdateUser({ ...updateUser, name: e.target.value })}
                            className="mt-2 p-2 border rounded w-full"
                        />
                        <input
                            type="password"
                            placeholder="新しいパスワード"
                            value={updateUser.password}
                            onChange={(e) => setUpdateUser({ ...updateUser, password: e.target.value })}
                            className="mt-2 p-2 border rounded w-full"
                        />
                        <button
                            onClick={handleUpdateUser}
                            className="mt-2 px-4 py-2 bg-yellow-500 text-white rounded"
                        >
                            ユーザー更新
                        </button>
                    </div>

                    {/* ユーザー削除フォーム */}
                    <div className="mt-4 p-4 border rounded">
                        <h3 className="text-xl font-semibold">ユーザー削除</h3>
                        <input
                            type="number"
                            placeholder="ユーザーID"
                            value={deleteUserId}
                            onChange={(e) => setDeleteUserId(e.target.value)}
                            className="mt-2 p-2 border rounded w-full"
                        />
                        <button
                            onClick={handleDeleteUser}
                            className="mt-2 px-4 py-2 bg-red-500 text-white rounded"
                        >
                            ユーザー削除
                        </button>
                    </div>

                    {/* ユーザー一覧の表示 */}
                    {users.length > 0 && (
                        <div className="mt-4">
                            <h3 className="text-xl font-semibold">ユーザー一覧:</h3>
                            <table className="min-w-full mt-2 border">
                                <thead>
                                    <tr>
                                        <th className="border px-4 py-2">ID</th>
                                        <th className="border px-4 py-2">名前</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.map((user) => (
                                        <tr key={user.id}>
                                            <td className="border px-4 py-2">{user.id}</td>
                                            <td className="border px-4 py-2">{user.name}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                {/* ブランクページのコンテンツ */}
            </main>
        </>
    );
}