import chainlit as cl
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import asyncio
import time
import functools
from web_search import WebSearch

"""
LangChain のコールバックを使わずに Python の標準機能でコールバックとイベントハンドラーを実装
"""

# こちらのコードはHTML要素を動的に生成するためのヘルパー関数と、特定のHTMLタグに関するショートカットを定義しています。
def elem(name: str, cls: str = "", attr: Dict[str, str] = {}, **attr_dic: str):
    """
    指定されたHTML要素を生成する関数です。

    Parameters:
        name (str): 生成するHTML要素の名前。 div や span など。
        cls (str): 要素に適用するクラス名。省略可能。
        attr (Dict[str, str]): 属性とその値を持つ辞書。省略可能。
        **attr_dic (str): 任意の数の追加属性をキーワード引数として受け取ります。

    Returns:
        function: 子要素を引数として受け取り、完全なHTML要素を文字列として返す関数。
    """
    all_attr = {**attr, **attr_dic}
    if cls:
        all_attr.update({"class": cls})

    attr_str = ""
    if len(all_attr) > 0:
        attr_str += "".join(f' {k}="{v}"' for k, v in all_attr.items())

    def inner(*children: str):
        """
        生成したHTML要素の子要素を設定する内部関数。

        Parameters:
            *children (str): 子要素の内容。

        Returns:
            str: 完全なHTML要素を表す文字列。

        例:
        f"<{name}{attr_str}>{children_str}</{name}>" は
            name         → div
            attr_str     → class="tw-atta-key"
            children_str → Plan
        になる。

        """
        children_str = "".join(children)
        return f"<{name}{attr_str}>{children_str}</{name}>"

    return inner


div = functools.partial(elem, "div")
span = functools.partial(elem, "span")


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
        self.start(f"{self.role_name} の処理を開始します")

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

    def update_message(self, previous_message: str, updated_message: str, is_end: bool = True):
        """
        メッセージ更新イベントを発行します。

        :param previous_message: 上書きしたい対象のメッセージ
        :param updated_message:  上書きしたいメッセージ
        :param is_end: メッセージが終了したかどうか
        """
        assert not self.message_is_end, "Cannot update message when update is finished"
        self.message_is_end = is_end
        update_message_event = {
            'type': 'update_message',
            'previous_message': previous_message,
            'updated_message': updated_message,
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



# メッセージ更新をリアルタイムでUIに反映するハンドラー
class ChainLitMessageUpdater(SessionEventHandler):
    """
    ChainLitを使用して、セッション中のイベントに応じてUIをリアルタイムで更新するハンドラーです。
    """
    def __init__(self, root_step: cl.Step):
        """
        ハンドラーを初期化し、親ステップを設定します。

        :param root_step: 親ステップとなる ChainLit のステップオブジェクト
        """        
        self.root_step = root_step
        # 子ステップを作成する理由
        # 親ステップ(root_step)が上書きされちゃうので、子ステップ(cur_step)をネストして、子ステップの表示を更新する
        self.cur_step: Optional[cl.Step] = None
        # prev_content_delete で使うための変数
        self.prev_content: str = None
        self.suppress_blinking_cursor()  # あってもなくても見た目変わらなかったのでどっちでも良さそう


    def suppress_blinking_cursor(self):
        cl.run_sync(self.root_step.stream_token(""))
        if self.cur_step is not None:
            cl.run_sync(self.cur_step.stream_token(""))


    def handle(self, event):
        """
        イベントを処理し、UIを更新します。

        :param event: イベント情報を含む辞書
        """        
        event_type  = event['type']
        is_sequence = event['is_sequence']
        cl.run_sync(self.root_step.stream_token(f"親ステップに表示される内容です。{event['role']}🧑🏽‍💻 が処理中……", True))   # 親ステップに表示される内容。ここの表示は上書きするようにする


        # イベントを受け取り、UIをリアルタイムで更新
        # イベントの種類に応じて処理を分岐
        if event_type == 'start':
            # 子ステップを開始（ネスト）
            self.cur_step = cl.Step(name=event['role'], show_input=True)
            cl.run_sync(self.cur_step.__aenter__())
            content = f"🟢 {event['message']}\n" if is_sequence else f"\n🟢 {event['message']}\n"    # is_sequence が False ならストリーミングトークンが続きとして出力されるので、先頭に改行コードを追加して、改行してからその続きを出力させる
            cl.run_sync(self.cur_step.stream_token(content, is_sequence))
            self.prev_content = content    # コンテンツを更新したら delete するために直前のメッセージを記憶しておく。エラーイベントとエンドイベントのときは更新しない。
            self.root_step.output = f"{event['role']}のタスクを開始します"
            cl.run_sync(self.root_step.update())    # エージェントのタスクが開始したら親ステップのメッセージを更新する
        elif event_type == 'progress':
            # 進捗状況を子ステップに表示
            if self.cur_step:
                content = f"🛠️ {event['message']}\n" if is_sequence else f"\n🛠️ {event['message']}\n"
                cl.run_sync(self.cur_step.stream_token(content, is_sequence))
                self.prev_content = content
        elif event_type == 'status':
            # ステータスメッセージを子ステップに表示
            if self.cur_step:
                content = f"ステータス: {event['message']}\n" if is_sequence else f"\nステータス: {event['message']}\n"
                if '[doing]' in event['message']:
                    content = event['message'].replace('[doing]','')
                    content = span("task-item pending")(content)
                elif '[done]' in event['message']:
                    if self.prev_content:
                        """
                        # pending だったタスクが completed になっているはずなので、ステータスをアップデートする
                        # step1: 消す
                        self.cur_step.output = self.cur_step.output[:-len(self.prev_content)]
                        # step2: completed に変更する。念の為 self.prev_content は上書きせず別の変数を使う
                        prev_content = self.prev_content.replace('pending','completed')
                        # step3: completed に変えたものを追加してアップデートする
                        self.cur_step.output += prev_content
                        cl.run_sync(self.cur_step.update())
                        # step4: 特殊トークンを削除して新しいタスクを追加
                        content = event['message'].replace('[done]','')
                        content = span("task-item completed")(content)                        
                        """
                        # 上記の処理をもっとシンプルにした
                        # pending だった一個前のタスクを削除する
                        self.cur_step.output = self.cur_step.output[:-len(self.prev_content)]
                        cl.run_sync(self.cur_step.update())
                        # 特殊トークン[done] を削除して新しいタスクを追加
                        content = event['message'].replace('[done]','')
                        content = span("task-item completed")(content)
                cl.run_sync(self.cur_step.stream_token(content, is_sequence))
                self.prev_content = content
        elif event_type == 'update_message':
            # メッセージの更新を子ステップに表示
            if self.cur_step:
                # 更新前のメッセージには doing が入っている想定
                if '[doing]' in event['previous_message']:
                    previous_message_content = event['previous_message'].replace('[doing]','')
                    previous_message_content = span("task-item pending")(previous_message_content)
                else:
                    previous_message_content = event['previous_message']

                # 更新後のメッセージには done が入っている想定
                if '[done]' in event['updated_message']:
                    updated_message_content = event['updated_message'].replace('[done]','')
                    updated_message_content = span("task-item completed")(updated_message_content)
                else:
                    updated_message_content = event['updated_message']

                self.cur_step.output = self.cur_step.output.replace(previous_message_content, updated_message_content)
                cl.run_sync(self.cur_step.update())
                self.prev_content = updated_message_content

                if event.get('is_end', False):
                    # メッセージ更新が終了した場合、ステップを終了
                    cl.run_sync(self.cur_step.__aexit__(None, None, None))
                    self.cur_step = None
        elif event_type == 'prev_content_delete':
            # 直前のコンテンツを削除する
            if self.cur_step:
                self.cur_step.output = self.cur_step.output[:-len(self.prev_content)]
                cl.run_sync(self.cur_step.update())
        elif event_type == 'error':
            # エラーメッセージを子ステップに表示し、ステップを終了
            if self.cur_step:
                content = f"❌ {event['message']}\n" if is_sequence else f"\n❌ {event['message']}\n"
                cl.run_sync(self.cur_step.stream_token(content, is_sequence))
                cl.run_sync(self.cur_step.__aexit__(None, None, None))
                self.cur_step = None
        elif event_type == 'end':
            # 処理完了メッセージを子ステップに表示し、ステップを終了。親ステップの表示も更新する
            if self.cur_step:
                content = f"✅ {event['message']}\n" if is_sequence else f"\n✅ {event['message']}\n"
                cl.run_sync(self.cur_step.stream_token(content, is_sequence))
                cl.run_sync(self.cur_step.__aexit__(None, None, None))
                self.cur_step = None
                self.root_step.output = f"{event['role']}のタスクが完了しました"
                cl.run_sync(self.root_step.update())    # エージェントのタスクが終了したら親ステップのメッセージを更新する
        else:
            # その他のイベント
            if self.cur_step:
                content = f"その他のイベント: {event['message']}\n" if is_sequence else f"\nその他のイベント: {event['message']}\n"
                cl.run_sync(self.cur_step.stream_token(content, is_sequence))
                self.prev_content = content


# セッションを管理するクラス
class Session:
    """
    ユーザーとのセッションを管理し、メッセージの処理やイベントの発行を行います。
    """
    def __init__(self):
        """
        セッションを初期化し、イベントエミッターを作成します。
        """        
        self.event_emitter = SessionEventEmitter()
        self.event_emitter.current_round_id = cl.user_session.get("id")

    def send_message(
        self,
        message: str,
        event_handler: Optional[SessionEventHandler] = None,
        files: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        ユーザーからのメッセージを処理し、必要なイベントを発行します。

        :param message: ユーザーからのメッセージ文字列
        :param event_handler: イベントを処理するハンドラー
        :param files: 添付ファイルのリスト（使用しない場合はNone）
        :return: 処理結果のメッセージ
        """

        def run_async_safely(coro):
            """この関数は、同期コンテキストと非同期コンテキストの両方で
               非同期コードを実行するのに役立ちます。"""
            try:
                return asyncio.run(coro)
            except RuntimeError:
                loop = asyncio.get_event_loop()
                return asyncio.ensure_future(coro)


        # 呼び出すロールを検討する関数
        async def async_process():
            async with cl.Step(name="プランナーエージェント(ロールを検討する)") as RoleThinkingStep:

                RoleThinkingStep.input  = message + " ← ユーザークエリ"
                await RoleThinkingStep.stream_token("ユーザークエリを分析してどのエージェントを呼び出すか考え中……", True)

                # ここにクエリを分析する処理
                # 遅延でシミュレート
                await cl.sleep(6)
                print("TaskWeaver の実装を踏襲しているので呼び出すエージェントが 1 つになっているが、ここを LLMcompiler にすると良さそう")

                await RoleThinkingStep.stream_token("AutoDocuMentor Agent を呼び出すことに決定しました", True)
                worker_instances = WebSearch(self.event_emitter)

                await cl.sleep(3)

            return worker_instances



        with self.event_emitter.handle_events_ctx(event_handler):
            
            worker_instances = run_async_safely(async_process())
            worker_response = worker_instances.reply(message)
            return worker_response



@cl.on_chat_start
async def on_chat_start():
    # チャットが始まるごとにセッションを初期化する。つまり、ブラウザリロードすると新しいセッション id が発行される
    session = Session()
    cl.user_session.set("session", session)

    await cl.Message(f"ようこそ!\ncurrent session id: {session.event_emitter.current_round_id}").send()

    # Nest Steps やってみた。親ステップは強制的に実行している
    async with cl.Step(name="親ステップ") as parent_step:
        parent_step.input = "Parent step input"

        # 条件分岐
        if parent_step.input == "Parent step input":
            # 真なら子ステップを実施
            async with cl.Step(name="子ステップ") as child_step:
                child_step.input = "Child step input"
                child_step.output = "Child step output"

        parent_step.output = "Parent step output"



# メイン関数：ユーザーメッセージの処理
@cl.on_message
async def main(message: cl.Message):

    session = cl.user_session.get("session")

    # メッセージ送信前にローダーを表示
    async with cl.Step(name="プランナーエージェント", show_input=True) as root_step:
        # 非同期でメッセージを送信。handle_events_ctx の結果を受け取る
        response = await cl.make_async(session.send_message)(
            message=message.content,
            event_handler=ChainLitMessageUpdater(root_step),
        )
        # 最終的なレスポンスを表示
        cl.run_sync(root_step.stream_token(f"\n最終的な結果\n{response}", True))   # 親ステップに表示される内容。True なので上書きされる
        await cl.Message(
            author="プランナーエージェント",
            content="終わりました。",
        ).send()




# このスクリプトが直接実行された場合の処理を記述します。
# スクリプトがモジュールとして他のファイルからインポートされたときには、このブロック内のコードが実行されないようにしています。
if __name__ == "__main__":
    # chainlitのコマンドラインインターフェースからrun_chainlitをインポート
    from chainlit.cli import run_chainlit

    # このファイルをchainlitアプリケーションとして起動する関数を呼び出します。
    # __file__は現在のスクリプトファイルの名前を指します。
    run_chainlit(__file__)