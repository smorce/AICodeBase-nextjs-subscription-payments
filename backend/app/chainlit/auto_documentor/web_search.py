# ========================================================
# メモ
# ========================================================

# API キーの入力はmainで実行するときに以下のように入力すればOK
# os.environ["OPENAI_API_KEY"] = "～～～"
# os.environ["GEMINI_API_KEY"] = "～～～"    # GEMINI_API_KEY でOK
# os.environ["TAVILY_API_KEY"] = "～～～"    # Free のキーを入手した
# os.environ["LANGCHAIN_API_KEY"] = "～～～"

# task.json の置き場所
# task_json_path = os.path.join(os.getcwd(), 'app', 'chainlit', 'auto_documentor','task.json')
# task_json_path: /app/app/chainlit/auto_documentor/task.json

import asyncio
import json
import os
import time
from uuid import uuid4
from dotenv import load_dotenv


# Run with LangSmith if API key is set
is_LangSmith = True
if is_LangSmith:
    unique_id = uuid4().hex[0:8]
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = f"Tracing Walkthrough - {unique_id}"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    # os.environ["LANGCHAIN_API_KEY"] = ""   # ★APIキーを入れる
load_dotenv()

# モジュールをインポートするためにパスの追加が必要。これを入れてもカレントディレクトリは変わらない。
# 以下は各ファイルで必要
from path_setup import setup_paths
setup_paths()


task_json_path = os.path.join(os.getcwd(), 'app', 'chainlit', 'auto_documentor','task.json')



# 元のコード。一旦消してみる。
# suppress asyncio runtime warning
# if sys.platform == "win32":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# # suppress tqdm message
# os.environ["TQDM_DISABLE"] = "True"


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

class WebSearch():
    """description:
        - WebSearchは検索エンジンを使ってクエリから情報を検索することができます。検索結果に基づいてレポートを作成することもできます。
        - プランナーはユーザーのクエリをWebSearchロールに適した質問形式に変換します。これは常に行われます。
            - 例 ユーザー入力： 「健康に良い食事のレシピを教えてください： 「健康に良い食事のレシピは何ですか？」
        - プランナーは、元のクエリが不十分だと感じたら、それを修正することができます。
        - プランナーは一度に1つのクエリしか送信できません。複数の問い合わせがある場合は、すべて質問形式に変換してください。"""
    def __init__(
        self,
        event_emitter: SessionEventEmitter,
    ):
        self.event_emitter = event_emitter

        self.researcher = None    # GPT-researcher を使っている。元々あった Agent がこれで、そこにその他のマルチエージェントが足された。マルチエージェントで使うモデルは task.json に書かれ、self.researcher の設定は config に書かれている
        # 以下が後から追加されたマルチエージェントたち
        self.writer = None
        self.editor = None
        self.publisher = None
        self.powerpointdesigner = None
        
        self.output_dir = None
        self.task = None
        self.query = None


    def init_research_team(self):
        try:
            from writer import WriterAgent
            from editor import EditorAgent
            from researcher import ResearchAgent
            from publisher import PublisherAgent
            from memory.research import ResearchState

            from langgraph.graph import StateGraph, END

            # -----------------------------------------------------
            # task.json の model は web_search/utils/llms.py で使うモデルのこと。LLM は OpenRouter や ChatGoogleGenerativeAI を使うようにしたので、そのやり方で指定する。
            # リサーチャーだけ異なる実装なので、使う LLM は config.py で設定する。
            # -----------------------------------------------------
            with open(task_json_path, 'r') as f:
                # これはリサーチャー以外のマルチエージェントで使う LLM                
                task = json.load(f)

            task["query"] = self.query  # user_input
            self.task = task
            
            self.output_dir = os.path.join(os.getcwd(), '.files', self.event_emitter.current_round_id, task.get('query')[0:40])
            os.makedirs(self.output_dir, exist_ok=True)


            # エージェントの初期化
            self.writer     = WriterAgent()
            self.editor     = EditorAgent(self.task)
            self.researcher = ResearchAgent()
            self.publisher  = PublisherAgent(self.output_dir)


            # ResearchState を持つ Langchain StateGraph を定義
            workflow = StateGraph(ResearchState)
            # memory/research.py で扱えるデータを定義している

            # Add nodes for each agent
            workflow.add_node("browser",    self.researcher.run_initial_research)
            workflow.add_node("planner",    self.editor.plan_research)
            workflow.add_node("researcher", self.editor.run_parallel_research)
            workflow.add_node("writer",     self.writer.run)
            workflow.add_node("publisher",  self.publisher.run)

            workflow.add_edge('browser',    'planner')
            workflow.add_edge('planner',    'researcher')
            workflow.add_edge('researcher', 'writer')
            workflow.add_edge('writer',     'publisher')

            # set up start and end nodes
            workflow.set_entry_point("browser")
            workflow.add_edge('publisher', END)

            print("デバッグ：ワークフローdone！")

            return workflow

        except Exception as e:
            raise Exception(f"Failed to initialize the plugin due to: {e}")

    def reply(self, user_input: str) -> str:

        self.query = user_input
        isOverrideChildStreamingToken = False

        from utils.views import print_agent_output
        # PostEventProxy を作成。is_sequence = False でストリーミングトークンが続きに出力される
        post_proxy = self.event_emitter.create_post_proxy(role_name='AutoDocuMentor Agent',
                                                        is_sequence=isOverrideChildStreamingToken)
        


        # # ディレクトリ構造を出力する関数
        # def print_directory_structure(directory, indent=0):
        #     for root, dirs, files in os.walk(directory):
        #         level = root.replace(directory, '').count(os.sep)
        #         indent = ' ' * 4 * level
        #         print(f"{indent}{os.path.basename(root)}/")
        #         sub_indent = ' ' * 4 * (level + 1)
        #         for f in files:
        #             print(f"{sub_indent}{f}")

        # print_directory_structure("/app")

        print("デバッグ writer1：", self.writer)
        if self.writer is None:
            research_team = self.init_research_team()
            print("デバッグ　リサーチチーム：", research_team)      # 初回だけ呼び出された。そのまま writer が残っていた
        print("デバッグ writer2：", self.writer)

        async def async_research(chain, task, post_proxy):
            """
            非同期でリサーチグラフを実行する関数。

            Args:
                chain: GPTリサーチャーの LangGraph オブジェクト。
                task: タスク情報を含む辞書。
                post_proxy: PostProxyオブジェクト。

            Returns:
                ResearchState クラス: リサーチグラフを実行した結果
            """
            # リサーチグラフの実行
            # Publisher の generate_layout で作成した layout が result["report"] に格納されている
            result = await chain.ainvoke({"task": task, "post_proxy": post_proxy})          # ★ research_agent.run_initial_research に task と post_proxy のデータを渡す。渡されていない title や conclusion などは None になる。どんなデータを渡せるかは memory/research.py で定義している。
            return result


        # def run_async_in_loop(coro):
        #     """
        #     既存のイベントループ内で非同期コルーチンを実行する関数。
        #         1. asyncio.get_event_loop を使って現在のイベントループを取得します。
        #         2. イベントループが既に走っているかどうかを確認します (loop.is_running()).
        #         3. 走っている場合、asyncio.ensure_future を使って非同期コルーチンをタスクとしてスケジュールし、その結果を loop.run_until_complete を使って待機します。
        #         4. 走っていない場合、そのまま loop.run_until_complete を使って非同期コルーチンを実行します。

        #     Args:
        #         coro: 実行する非同期コルーチン。

        #     Returns:
        #         任意: コルーチンの実行結果。
        #     """
        #     loop = asyncio.get_event_loop()
        #     if loop.is_running():
        #         # 既存のイベントループが実行中の場合、コルーチンをタスクとしてスケジュールし、完了を待機
        #         future = asyncio.ensure_future(coro)
        #         loop.run_until_complete(future)
        #         return future.result()
        #     else:
        #         # 既存のイベントループが実行中でない場合、そのままコルーチンを実行
        #         return loop.run_until_complete(coro)


        # ★[2024/10/05] 安全なやり方に変えてみた。大丈夫か？
        def run_async_in_loop(coro):
            """
            非同期コルーチンを既存のイベントループ内で実行する。

            この関数は、与えられたコルーチンを現在のイベントループで実行します。
            イベントループの状態に応じて、異なる方法でコルーチンを処理します。

            Args:
                coro (coroutine): 実行する非同期コルーチン。

            Returns:
                Union[asyncio.Task, Any]: イベントループが実行中の場合はTask、
                そうでない場合はコルーチンの実行結果を返します。

            Behavior:
                - イベントループが既に実行中の場合:
                コルーチンを新しいTaskとしてスケジュールし、そのTaskを返します。
                - イベントループが実行中でない場合:
                コルーチンを直接実行し、その結果を返します。

            Note:
                この関数は、同期コンテキストと非同期コンテキストの両方で
                非同期コードを実行するのに役立ちます。
            """
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 既存のイベントループが実行中の場合、コルーチンをタスクとしてスケジュールし、Future を返す
                return asyncio.create_task(coro)
            else:
                # 既存のイベントループが実行中でない場合、そのままコルーチンを実行
                return loop.run_until_complete(coro)



        try:

            post_proxy.update_status("[doing]Research Team🕵️‍♀️ を編成する")

            # グラフをコンパイルする
            chain = research_team.compile()
            post_proxy.update_status("[done]Research Team🕵️‍♀️ を編成する")


            print_agent_output(f"Starting the research process for query '{self.task.get('query')}'...", "MASTER")


            # with post_proxy.override_sequence_temporarily(True):
                # 一度でも True にすると False にして出したものも全部消えちゃうっぽい
                # なので、一回 .send() で確定させる必要があるかも
                # → is_sequence が 上書きされたか？フラグ を作って send で確定させて、新しいステップを開始して、stream_token(content, True)して、ステップを終了させる。という処理になりそう。
                # → かなり複雑化するのでやめた方が良い。新しいステップが開始する見え方も不自然なので。実装したけど、基本的に 途中で override_sequence_temporarily(True) する処理は使わないようにする。
                # post_proxy.progress("デバッグ 一時的に is_sequence を True にして上書きする 1")
                # post_proxy.update_status("デバッグ 一時的に is_sequence を True にして上書きする 2")
                
                # ↓ もっと簡単に実装した。直前のコンテンツを削除して続きを生成する

            # time.sleep(6)
            # post_proxy.progress("prev_content_delete で 'この文章' を削除します")
            # time.sleep(6)
            # post_proxy.prev_content_delete()
            # post_proxy.update_status("上書きしました！")



            # ------------------------------------

            # 非同期処理を実行
            print_agent_output("デバッグ：リサーチします！", "MASTER")
            result = run_async_in_loop(async_research(chain, self.task, post_proxy))
            print_agent_output("デバッグ：リサーチ完了！", "MASTER")

            # print("result に何が入っている？？")
            # print(result)


            async def async_powerpointdesigner(powerpointdesigner, post_proxy):
                """
                非同期で PowerPointDesignerAgent を実行する関数。
                """
                # post_proxy = await powerpointdesigner.run(post_proxy)
                # return post_proxy
                # 参照なので上記は不要かも。★ 一旦消してみておかしかったら復活させる

                await powerpointdesigner.run(post_proxy)



            # 調査が完了した後にパワーポイントデザイナーを呼び出す
            from powerpointdesigner import PowerPointDesignerAgent
            powerpointdesigner = PowerPointDesignerAgent(self.output_dir)
            # post_proxy = run_async_in_loop(async_powerpointdesigner(powerpointdesigner, post_proxy))              # output_dir からマークダウンファイルを読み込む。
            # 参照なので上記は不要かも。★ 一旦消してみておかしかったら復活させる
            
            
            run_async_in_loop(async_powerpointdesigner(powerpointdesigner, post_proxy))              # output_dir からマークダウンファイルを読み込む。
            
            
            post_proxy.progress("ちゃんと更新されているなら、この文章が最後に表示されるはず")
            
            
            # 意図的にエラーを発生させる
            # raise Exception("意図的なエラー発生のため停止します")


        except Exception as e:
            print(f"Failed to reply due to: {e}")



        # 意図的にエラーを発生させる
        # raise Exception("意図的なエラー発生のため停止します")


        print("デバッグ：完了しました")
        # 処理の終了を通知
        post_proxy.end("リサーチプロセスは完了しました！ついでにレポートも作成しました！")

        # 最終的なレスポンスを返す
        return f"round_id = {post_proxy.round_id}: {post_proxy.role_name}🧑🏽‍💻 の処理が完了しました。"



    # def close(self) -> None:
    #     if self.driver is not None:
    #         self.driver.quit()
    #     super().close()