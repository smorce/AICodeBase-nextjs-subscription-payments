import os
import base64
import json
import re
import urllib.parse
import ntplib
import time
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Optional, Any, List
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.callbacks import BaseCallbackHandler, StdOutCallbackHandler
from langchain_core.runnables import RunnableConfig

import hashlib
from pydantic import BaseModel, Field
import yaml
from yaml.loader import SafeLoader

import chainlit as cl
import jwt
from supabase import create_client, Client

# 現在のディレクトリをこのファイルが存在するディレクトリに変更します
os.chdir(os.path.dirname(__file__))

# 現在のディレクトリ
CURRENT_DIR = os.getcwd()

# .envファイルへのパスを構築
env_path = os.path.join(CURRENT_DIR, '..', '..', '.env')

# .envファイルが存在するか確認
if os.path.exists(env_path):
    # .envファイルを読み込む
    load_dotenv(dotenv_path=env_path)
    print(".env file loaded successfully!")
else:
    print(f"Warning: .env file not found at {env_path}")

# 環境変数からSupabaseのJWTシークレットを取得
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
if not SUPABASE_JWT_SECRET:
    print("エラー: SUPABASE_JWT_SECRET が環境変数に設定されていません。")
    # エラーハンドリングまたは終了処理
    exit(1)
print(f"デバッグ SUPABASE_JWT_SECRET = {SUPABASE_JWT_SECRET}")



# 環境変数から SUPABASE_URL を取得
SUPABASE_URL = os.getenv("SUPABASE_URL")
if not SUPABASE_URL:
    print("エラー: SUPABASE_URL が環境変数に設定されていません。")
    # エラーハンドリングまたは終了処理
    exit(1)
print(f"デバッグ SUPABASE_URL = {SUPABASE_URL}")

# 環境変数から SUPABASE_KEY を取得
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_KEY:
    print("エラー: SUPABASE_KEY が環境変数に設定されていません。")
    # エラーハンドリングまたは終了処理
    exit(1)
print(f"デバッグ SUPABASE_KEY = {SUPABASE_KEY}")

# Supabaseクライアントの初期化。SUPABASE_KEY は ANON_KEY を指す
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



# ===================================================================



system_prompt = "あなたは非常に賢いAIアシスタントです。"

welcome_message = """レポートの目次を相談して決める プログラム へようこそ！

以下の質問に答えてください：
レポートの目次は既に決まっていますか？
   - はい → 1. 目次を教えてください。
   - いいえ → 2. どのようなテーマやトピックを取り扱う予定ですか？

"""
# ===================================================================



# ステップの実行結果は必ず画面上に表示される仕様。多分リターンすると表示されるのかも。デコレーターの引数で表示を制御するフラグがあれば消すことはできそう
@cl.step(name="Calling LLM")
async def call_model(user_input: str):
    # -------------------------------------------------------------------------
    # ストリーミング
    # -------------------------------------------------------------------------
    # ストリーミング表示のイメージ。やるなら ChatGoogleGenerativeAI のストリーミングを調べないといけない
    # 空のメッセージを送信して、ストリーミングする場所を用意しておく
    # agent_message = cl.Message(content="")
    # await agent_message.send()

    ### ここを ChatGoogleGenerativeAI の LCEL記法(streaming) に置き換え
    # stream = await client.chat.completions.create(
    #     messages=message_history, stream=True, **settings
    # )

    # async for part in stream:
    #     if token := part.choices[0].delta.content or "":
    #         await agent_message.stream_token(token)

    # 空っぽの部分をガンガン ストリーミングで更新していく
    # await agent_message.update()
    # -------------------------------------------------------------------------


    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-exp-0827",
                                   temperature=1,
                                   streaming=True
                                   )
    prompt = ChatPromptTemplate.from_messages(
        [
            # 毎回必ず含まれるSystemプロンプトを追加
            SystemMessage(content=system_prompt),
            # ConversationBufferWindowMemoryをプロンプトに追加
            # MessagesPlaceholder(variable_name="history"),       # シンプルに実装するため一旦削除
            # ユーザーの入力をプロンプトに追加
            HumanMessagePromptTemplate.from_template("{user_input}"),
        ]
    )

    output_parser = StrOutputParser()

    # LCEL記法でchainを構築
    chain = prompt | model | output_parser


    response = chain.invoke({"user_input": user_input})


    # 良い感じに画面上に表示されることを確認した
    # await cl.Message(content=f"User: {user_input}").send()
    # await cl.Message(content=f"Assistant: {response}").send()

    return response


# ===================================================================
@cl.step(name="実行ツール")
async def action_input_display(action_input: str):
    """Toolを呼び出してActionを実行した時の実行情報をStepに表示する
    Args: action_input(ToolInvocation)
    Return: display_message(Str)
    """
    tool = "【step1】 あああ"
    tool_input = "【step1】 いいい"

    display_message = f"""
    tool: {tool}
    tool_input: {tool_input}
    """
    return display_message

@cl.step(name="ツール結果")
async def action_result_display(action_result: str):
    """Toolを呼び出してActionを実行した時の実行結果をStepに表示する
    Args: action_result(FunctionMessage)
    Return: display_message(Str)
    """
    action_result = "【step2】 ううう"

    display_message = f"""
    tool_result: {action_result}
    """
    return display_message


# --------------------------------------------------
# Stream the Output
# --------------------------------------------------
# root: ユーザーメッセージの下にステップをネストするかどうか
@cl.step(name="【シンプルにストリーミングするだけ】Gemini-1.5-flash-exp-0827", type="llm", root=True)
async def streaming_call_llm(user_input: str):

    # セッティング
    cur_step = cl.context.current_step
    cur_step.input = user_input
    full_txt = ""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessagePromptTemplate.from_template("{user_input}"),
        ]
    )

    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-exp-0827",
                                    temperature=1,
                                    streaming=True,
                                    )

    output_parser = StrOutputParser()

    chain = prompt | model | output_parser
    
    async for chunk in chain.astream({"user_input": user_input}):
        # ステップの出力をストリームする
        chunk = f'<font color="red">{chunk}</font>'
        full_txt += chunk
        await cur_step.stream_token(chunk)

    return full_txt


# ★テストとして以下を書いたが実際には TaskWeaver のコードを流用してコンテンツを HTML 化したい
html_content = """<div class="tw-atta">
    <div class="tw-atta-header">
        <div class="tw-atta-key">Plan</div>
        <div class="tw-atta-id">タスクid 1</div>
    </div>
    <div class="tw-atta-cnt">
        <div class="tw-plan">
            <div class="tw-plan-item">
                <div class="tw-plan-idx">1</div>
                <div class="tw-plan-cnt">ファーストステップはこれ<span class="tw-end-cursor"></span></div>
            </div>
        </div>
    </div>
</div>

<div class="tw-status">
    <span class="tw-status-updating"><svg viewBox="22 22 44 44"><circle></circle></svg></span>
    <span class="tw-status-msg">Updating...</span>
</div>"""


# --------------------------------------------------
# make_async と langchain における コールバック
# make_async は処理が終わったら表示が消えてしまう仕様。結果は見せずに、「今YYYを呼び出してXXXを処理しています」という見え方をさせるためだけの機能。
# --------------------------------------------------
# root: ユーザーメッセージの下にステップをネストするかどうか
@cl.step(name="Planner Agent【make_asyncとコールバック】", type="llm", root=True)
async def call_makeAsync_and_callbacks(user_input: str):

    # セッティング
    cur_step = cl.context.current_step
    cur_step.input = user_input
    full_txt = ""

    # ---------------------------------------------------
    # イベントハンドラー
    # ---------------------------------------------------

    # langchain における コールバック
    # コールバックハンドラの各メソッドの対応しているイベントはあらかじめ決まっている。ストリーミングなら「on_llm_new_token」
    # https://zenn.dev/umi_mori/books/prompt-engineer/viewer/langchain_callbacks
    
    # コールバックの方法：ストリーミングを行うための「on_llm_new_token」をオーバーライドして、メソッドとして定義して使う
    class StreamHandler(BaseCallbackHandler):
        async def on_llm_new_token(self, token: str, **kwargs) -> None:
            # トークンが生成される度にこの関数が呼び出される。TaskWeaver では handle_post メソッドが呼び出された
            print(f"ストリーミングハンドラーの呼び出し！ token = {token}")
            await cl.Message(content="【ストリーミングハンドラー】の呼び出し！", author="Planner Agent【make_asyncとコールバック】").send()

    # 別の種類も追加してみた
    class ChatStartHandler(BaseCallbackHandler):
        async def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[BaseMessage]], **kwargs) -> None:
            print("チャットスタートモデルの呼び出し！")
            await cl.Message(content="【チャットスタートモデル】の呼び出し！", author="Planner Agent【make_asyncとコールバック】").send()
            elements = [
                cl.Text(content=html_content, display="inline")
            ]
            await cl.Message(
                    content="【チャットスタートモデルと一緒に呼び出し】Check out this text element!",
                    elements=elements,
                    author="Planner Agent【make_asyncとコールバック】",
                ).send()


    # ---------------------------------------------------



    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_prompt),
            HumanMessagePromptTemplate.from_template("{user_input}"),
        ]
    )
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-exp-0827",
                                    temperature=1,
                                    streaming=True,
                                    )

    output_parser = StrOutputParser()

    chain = prompt | model | output_parser

    # RunnableConfig に callbacks をキーとして callback オブジェクトのリストを設定
        # StdOutCallbackHandler(): コンソールに途中出力するためのイベントハンドラー
        # StreamHandler(): ストリーミング用のトークンが生成された時に呼び出されるイベントハンドラー
        # ChatStartHandler(): チャットモデル呼び出し時のイベントハンドラー
    config = RunnableConfig({'callbacks': [StdOutCallbackHandler(), StreamHandler(), ChatStartHandler()]})


    # 以下の処理中に特定のイベントに発火して callbacks のイベントハンドラーが呼び出される
    # 例えば、チャットモデルのスタート時やストリーミングトークンの出力時など
    async for chunk in await cl.make_async(chain.astream)(
            {"user_input": user_input},
            config=config,                 # ここで LangChain のコールバックを指定する
        ):
        # ステップの出力をストリームする
        # TaskWeaver は ここの chunk を HTML 化したものになっている気がする
        chunk = f'<font color="blue">{chunk}</font>'
        full_txt += chunk
        await cur_step.stream_token(chunk)   # root=False にするとココが表示されなくなる

    return full_txt




# ===================================================================
# 【ヘッダーによる認証・認可】

def extract_access_token(cookie_header: str):
    """
    Cookieヘッダー文字列から access_token と refresh_token を抽出する関数。

    Args:
        cookie_header (str): access_token と refresh_token を含むテキスト。URLエンコードされている可能性があります。

    Returns:
        dict: access_token と refresh_token をキーとする辞書。
              トークンが見つからない場合は、対応する値は None になります。
    """
    if not cookie_header:
        return None
    
    # URLデコード
    decoded_text = urllib.parse.unquote(cookie_header)
    
    # 正規表現パターンの定義
    access_token_pattern  = r'access_token":"([^"]+)"'  # access_token を抽出するための正規表現
    refresh_token_pattern = r'refresh_token":"([^"]+)"'  # refresh_token を抽出するための正規表現
    
    # access_token の抽出
    access_token_match = re.search(access_token_pattern, decoded_text)
    access_token = access_token_match.group(1) if access_token_match else None
    
    # refresh_token の抽出
    refresh_token_match = re.search(refresh_token_pattern, decoded_text)
    refresh_token = refresh_token_match.group(1) if refresh_token_match else None
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def decode_token_without_verification(token: str) -> dict:
    """
    JWTトークンを検証せずにデコードし、ペイロードの内容を返す。

    この関数は、トークンの署名を検証せずにペイロードをデコードするため、
    デバッグ目的でのみ使用すべきです。実際の認証には使用しないでください。

    Args:
        token (str): デコードするJWTトークン

    Returns:
        dict: デコードされたトークンのペイロード

    Raises:
        ValueError: トークンのフォーマットが無効な場合
    """
    # トークンをヘッダー、ペイロード、署名の3つの部分に分割
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("無効なトークンフォーマット")

    # ペイロード部分を取得
    payload = parts[1]

    # Base64のパディングを調整
    # Base64エンコードされた文字列の長さは4の倍数である必要があるため、
    # 必要に応じて'='を追加してパディングを行う
    payload += '=' * (-len(payload) % 4)

    # Base64デコードを行い、バイト列を取得
    decoded = base64.urlsafe_b64decode(payload)

    # デコードされたJSONをPythonの辞書に変換して返す
    return json.loads(decoded)


# JWTデコードが必要な場合は以下のように実装できます（使っていない）
def decode_jwt(access_token: str) -> Dict:
    try:
        return jwt.decode(
            access_token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"   # Supabaseのデフォルトは authenticated 。確認方法：Authentication ページ > Users で登録ユーザーが見える。アプリケーションにログインしているユーザーのレコードの一番右側の「…」をクリック > View user info でユーザー情報を確認できる
        )
    except jwt.ExpiredSignatureError:
        print("トークンの有効期限が切れています")
    except jwt.InvalidAudienceError:
        print("認証に失敗しました（Audience不一致）")
    except jwt.InvalidIssuedAtError:
        print("トークンの発行時刻が無効です")
    except jwt.InvalidTokenError as e:
        print(f"無効なトークン: {e}")
    except Exception as e:
        print(f"トークンのデコード中に予期せぬエラーが発生しました: {e}")
    return {}



def check_time_sync(ntp_server="pool.ntp.org", max_offset=1):
    client = ntplib.NTPClient()
    
    try:
        # NTPサーバーから時刻を取得
        response = client.request(ntp_server, version=3)
        
        # サーバー時刻
        server_time = datetime.fromtimestamp(response.tx_time)
        
        # クライアント(ローカル)時刻
        local_time = datetime.now()
        
        # 時差を計算(秒単位)
        time_offset = abs((server_time - local_time).total_seconds())
        
        print(f"サーバー時刻: {server_time}")
        print(f"ローカル時刻: {local_time}")
        print(f"時差: {time_offset:.2f} 秒")
        
        # 許容範囲内かチェック
        if time_offset <= max_offset:
            print("時刻は同期しています。")
            return True
        else:
            print(f"時刻が同期していません。許容範囲({max_offset}秒)を超えています。")
            return False
    
    except ntplib.NTPException as e:
        print(f"NTPサーバーとの通信エラー: {e}")
        return False



# ヘッダー認証は、ヘッダーを使用してユーザーを認証する簡単な方法です。通常、リバース プロキシに認証を委任するために使用されます。
@cl.header_auth_callback
def header_auth_callback(headers: Dict) -> Optional[cl.User]:

    # Cookieヘッダーからaccess_tokenを抽出（Cookieヘッダーに refresh_token も入っていたので refresh_token も取り出すことは可能）
    cookie_header = headers.get('Cookie', '') or headers.get('cookie', '')
    token_json    = extract_access_token(cookie_header)
    access_token  = token_json["access_token"]
    refresh_token = token_json["refresh_token"]


    # print(f"headers = {headers}")
    # print(f"cookie_header = {cookie_header}")


    # デバッグ
    if access_token:
        print(f"★access_token: {access_token}")  # ← 取得できている
    else:
        print("★access_tokenが見つかりません。")


    if not access_token:
        # アクセストークンが存在しない場合
        return None


    # デバッグ。トークンの内容を確認
    try:
        token_content = decode_token_without_verification(access_token)
        print("★Token content:", json.dumps(token_content, indent=2))
    except Exception as e:
        print(f"トークンのデコードに失敗しました: {e}")


    # 実行
    check_time_sync()


    try:
        # Supabaseを使用してセッションを検証
        # アクセストークンの検証をSupabaseのサーバー側で行う
        print("デバッグ1")
        response = supabase.auth.get_user(access_token)
        print("デバッグ2")
        user = response.user

        if user:
            return cl.User(
                identifier=user.email,
                metadata={"role": user.role, "provider": "supabase"}
            )
        else:
            print("有効なユーザーが見つかりません")
            return None

    except Exception as e:
        print(f"認証中にエラーが発生しました: {e}")
        return None



# ===================================================================


@cl.on_chat_start
async def on_chat_start():
    await cl.Message(welcome_message).send()


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



    cl.user_session.set("is_finish_flag", False)
    cl.user_session.set("counter", 0)



    # メッセージの履歴を保存するためのリストをセッションに保存
    cl.user_session.set("history", {"messages": []})



@cl.on_message
async def main(message: cl.Message):

    is_finish_flag = cl.user_session.get("is_finish_flag")

    # 初回実行なら真
    if not is_finish_flag:
        counter = cl.user_session.get("counter")
        counter += 1
        cl.user_session.set("counter", counter)
        await cl.Message(content=f"{counter}回目のメッセージです。").send()   # 画面上に出力: 1回目の返答


        # 会話の履歴を取得
        history = cl.user_session.get("history")
        await cl.Message(content=history).send()   # 画面上に出力: 2回目の返答


        # ============================================================
        # Step群
        # ============================================================
        # call_model はここ
        # user_input = "指示: 300文字程度の短い小説を書いてください。"
        user_input = message.content

        if user_input:
            # LLM を呼び出す
            ai_message = await call_model(user_input)



        # 実行Toolの情報を取得
        action_input = "使ったツールはこちらです"
        if action_input:
            # "実行ツール"のStep表示
            await action_input_display(action_input)
        action_result  = "使ったツールの実行結果はこちらです"
        if action_result:
            # "ツール結果"のStep表示
            await action_result_display(action_result)
        # ============================================================


        # ============================================================
        # Stepデコレータで LLM のストリーミング出力
        # ============================================================
        if user_input:
            # LLM を呼び出す
            ai_message = await streaming_call_llm(user_input)


        # ============================================================
        # make_async と langchain における コールバック
        # ============================================================
        if user_input:
            # LLM を呼び出す
            ai_message = await call_makeAsync_and_callbacks(user_input)




        # ============================================================

        # 最終的な応答を履歴に追加し、セッションに保存
        history["messages"].append(HumanMessage(content=user_input))
        history["messages"].append(AIMessage(content=ai_message))
        cl.user_session.set("history", history)

        await cl.Message(content=f"{ai_message}", author="assistant").send()   # 画面上に出力: 3回目の返答
        is_finish_flag = True
        cl.user_session.set("is_finish_flag", is_finish_flag)

    else:

        await cl.Message(content="AI: ご利用をありがとうございました。続けて入力することはできません。ブラウザをリロードするか新規チャットを開いてください。", author="assistant").send()




# このスクリプトが直接実行された場合の処理を記述します。
# スクリプトがモジュールとして他のファイルからインポートされたときには、このブロック内のコードが実行されないようにしています。
if __name__ == "__main__":
    # chainlitのコマンドラインインターフェースからrun_chainlitをインポート
    from chainlit.cli import run_chainlit

    # このファイルをchainlitアプリケーションとして起動する関数を呼び出します。
    # __file__は現在のスクリプトファイルの名前を指します。
    run_chainlit(__file__)