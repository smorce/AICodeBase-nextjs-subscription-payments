import os
from utils.views import print_agent_output
from utils.file_formats import write_md_to_ppt
from utils.llms import call_model


# ------------------------------------------------------------
# ★以下をモジュール化する
# ------------------------------------------------------------
from typing import Optional, List
from contextlib import contextmanager
# イベントハンドラーの基底クラス
class SessionEventHandler:
    """
    イベントを処理するための基本的なハンドラークラスです。
    すべてのカスタムハンドラーはこのクラスを継承します。
    """
    def handle(self, event):
        """
        イベントを処理するためのメソッドです。サブクラスでオーバーライドします。

        :param event: イベント情報を含む辞書
        """
        pass


# イベントを管理・発行するクラス
class SessionEventEmitter:
    """
    セッション中のイベントを管理し、登録されたハンドラーにイベントを発行します。
    """
    def __init__(self):
        """
        イベントエミッターを初期化し、ハンドラーのリストを作成します。
        """
        self.handlers: List[SessionEventHandler] = []
        self.current_round_id: Optional[str] = None  # 現在のラウンドIDを保持


    def emit(self, event):
        """
        登録されたすべてのハンドラーにイベントを発行します。

        :param event: イベント情報を含む辞書
        """
        for handler in self.handlers:
            handler.handle(event)


    def create_post_proxy(self, role_name: str, is_sequence: bool) -> 'PostEventProxy':
        """
        :param is_sequence: True でストリーミングトークンを上書きする。 False でストリーミングトークンが続きに出力される
        """
        assert self.current_round_id is not None, "Cannot create post proxy without a round in active"
        # from taskweaver.memory.post import Post

        return PostEventProxy(
            self,                    # SessionEventEmitter 自身を渡す。つまり、PostEventProxy は自身を作成した SessionEventEmitter インスタンスへの参照を保持することになる。
            self.current_round_id,
            role_name,
            is_sequence,
        )


    @contextmanager
    def handle_events_ctx(self, handler: Optional[SessionEventHandler] = None):
        """
        イベントハンドラーをコンテキスト内で登録・登録解除するためのコンテキストマネージャーです。

        :param handler: 登録するイベントハンドラー
        """
        if handler is None:
            yield
        else:
            self.register(handler)
            try:
                yield
            finally:
                self.unregister(handler)

    def register(self, handler: SessionEventHandler):
        """
        イベントハンドラーを登録します。

        :param handler: 登録するイベントハンドラー
        """
        self.handlers.append(handler)

    def unregister(self, handler: SessionEventHandler):
        """
        イベントハンドラーを登録解除します。

        :param handler: 登録解除するイベントハンドラー
        """
        self.handlers.remove(handler)




class PostEventProxy:
    """
    イベントを簡単に発行するためのプロキシクラスです。
    """
    def __init__(self, emitter: SessionEventEmitter, round_id: str, role_name: str, is_sequence: bool) -> None:
        """
        PostEventProxyを初期化します。

        :param emitter: イベントエミッター
        :param round_id: ラウンドID
        :param role_name: ロール名（ステップの名前として使用）
        :param is_sequence: True で ストリーミングトークンを上書きする。 False でストリーミングトークンが続きに出力される
        """
        # emitter は SessionEventEmitter インスタンス自身。参照を保持するので、こっちで更新すると伝搬する
        self.emitter = emitter
        self.round_id = round_id
        self.role_name = role_name
        self.is_sequence = is_sequence
        self.message_is_end = False
        # 初期化時にstartイベントを発行
        self.start(f"{self.role_name} の処理を開始します。")

    def start(self, message: str):
        """
        startイベントを発行します。

        :param message: 開始メッセージ
        """
        start_event = {
            'type': 'start',
            'message': message,
            'role': self.role_name,
            'is_sequence': self.is_sequence,
        }
        self.emitter.emit(start_event)

    def progress(self, message: str):
        """
        進捗更新イベントを発行します。

        :param message: 進捗メッセージ
        """
        progress_event = {
            'type': 'progress',
            'message': message,
            'role': self.role_name,
            'is_sequence': self.is_sequence,
        }
        self.emitter.emit(progress_event)

    def update_status(self, status: str):
        """
        ステータス更新イベントを発行します。

        :param status: ステータスメッセージ
        """
        status_event = {
            'type': 'status',
            'message': status,
            'role': self.role_name,
            'is_sequence': self.is_sequence,
        }
        self.emitter.emit(status_event)

    def update_message(self, message: str, is_end: bool = True):
        """
        メッセージ更新イベントを発行します。

        :param message: 更新するメッセージ
        :param is_end: メッセージが終了したかどうか
        """
        assert not self.message_is_end, "Cannot update message when update is finished"
        self.message_is_end = is_end
        update_message_event = {
            'type': 'update_message',
            'message': message,
            'role': self.role_name,
            'is_sequence': self.is_sequence,
        }
        self.emitter.emit(update_message_event)

    # update_attachment は不要
    # def update_attachment(
    #     self,
    #     message: str,
    #     type: Optional[AttachmentType] = None,
    #     extra: Any = None,
    #     id: Optional[str] = None,
    #     is_end: bool = True,
    # ) -> Attachment:
    #     from taskweaver.memory.attachment import Attachment

    #     if id is not None:
    #         attachment = self.post.attachment_list[-1]
    #         assert id == attachment.id
    #         if type is not None:
    #             assert type == attachment.type
    #         attachment.content += message
    #         attachment.extra = extra
    #     else:
    #         assert type is not None, "type is required when creating new attachment"
    #         attachment = Attachment.create(
    #             type=type,
    #             content=message,
    #             extra=extra,
    #             id=id,
    #         )
    #         self.post.add_attachment(attachment)
    #     self._emit(
    #         PostEventType.post_attachment_update,
    #         message,
    #         {
    #             "type": type,
    #             "extra": extra,
    #             "id": attachment.id,
    #             "is_end": is_end,
    #         },
    #     )
    #     return attachment

    def error(self, message: str):
        """
        エラーイベントを発行します。

        :param message: エラーメッセージ
        """        
        error_event = {
            'type': 'error',
            'message': message,
            'role': self.role_name,
            'is_sequence': self.is_sequence,
        }
        self.emitter.emit(error_event)

    def end(self, message: str):
        """
        終了イベントを発行します。

        :param message: 終了メッセージ
        """        
        end_event = {
            'type': 'end',
            'message': message,
            'role': self.role_name,
            'is_sequence': self.is_sequence,
        }
        self.emitter.emit(end_event)


    @contextmanager
    def override_sequence_temporarily(self, value: bool):
        """
        【正常に動くけど、使い所がないので基本的に使わない】
        一時的に is_sequence の値を変更するメソッド
        一度でも is_sequence を True にすると step.output がまるっと上書きされてしまうため
        False で表示していた部分も全て消えてしまう
        """
        original_value = self.is_sequence
        self.is_sequence = value
        try:
            yield
        finally:
            self.is_sequence = original_value


    def prev_content_delete(self):
        """
        直前のコンテンツを削除します。
        """        
        prev_content_delete_event = {
            'type': 'prev_content_delete',
            'message': None,
            'role': self.role_name,
            'is_sequence': self.is_sequence,
        }
        self.emitter.emit(prev_content_delete_event)

# ------------------------------------------------------------



class PowerPointDesignerAgent:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def load_latest_markdown(self, directory):
        """
        指定されたディレクトリから最新のマークダウンファイルを読み込み、その内容を返す関数。

        Args:
        directory (str): マークダウンファイルを検索するディレクトリのパス。

        Returns:
        str: 最新のマークダウンファイルの内容。ファイルが存在しない場合は None を返す。
        """
        # ディレクトリ内の全ファイルを取得し、マークダウンファイルのみをフィルタリング
        files = [f for f in os.listdir(directory) if f.endswith('.md')]

        # ファイルが存在するかどうかのチェック
        if not files:
            print("No markdown files found in the directory.")
            return None

        # ファイルの最終更新時刻を取得し、最新のものを見つける
        latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(directory, x)))

        # 最新のマークダウンファイルのパス
        latest_file_path = os.path.join(directory, latest_file)

        # ファイルを開いて内容を読み込む
        with open(latest_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        return content


    def convertToMarpContent(self, md_content):

        prompt = [{
            "role": "system",
            "content": "あなたは構造化された文章を Marp 形式にコンバートするプログラムです。"
        }, {
            "role": "user",
            "content": f"""以下の構造化された文章を Marp のスライド形式に変換してください。各セクションをスライドに分け、適切な見出しや箇条書きを使用してください。

### 構造化された文章 ###
{md_content}

### Marp 形式への変換例 ###

```markdown
---
marp: true
title: プレゼンテーションのタイトル
author: あなたの名前
date: 2024年4月27日
theme: default
paginate: true
---

# セクション1: はじめに

- ポイント1
- ポイント2
- ポイント3

---

# セクション2: 背景

## サブセクション1

- 詳細1
- 詳細2

---

## サブセクション2

- 詳細1
- 詳細2

---

# セクション3: 方法論

1. ステップ1
2. ステップ2
3. ステップ3

---

# セクション4: 結果

- 結果1
- 結果2
- 結果3

---

# セクション5: 結論

- 要点1
- 要点2
- 今後の展望
```

### 回答 ###"""
        }]

        marp_content = call_model(prompt=prompt, model="gemini-1.5-pro-002")

        return marp_content


    async def write_report_by_formats(self, md_content, output_dir):
        await write_md_to_ppt(md_content, output_dir)           # Marpで実装した。他の関数と合わせて非同期にした。


    async def run(self, post_proxy: PostEventProxy):
        print_agent_output(f"パワーポイントを作成中...", agent="POWERPOINTDESIGNER")
        post_proxy.update_status("[doing]PowerPointDesignerAgent📰: Pptx を作成する")

        # mdファイルを開いて内容を読み込む
        md_content = self.load_latest_markdown(self.output_dir)
        # mdファイルを Marp 用コンテンツにコンバートする
        marp_content = self.convertToMarpContent(md_content)
        # Pptx を作成して保存する
        await self.write_report_by_formats(marp_content, self.output_dir)
        post_proxy.update_status("[done]PowerPointDesignerAgent📰: Pptx を作成する")

        return post_proxy