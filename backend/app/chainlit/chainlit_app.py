import os
import base64
import json
from dotenv import load_dotenv
from typing import Dict, Optional
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

import hashlib
from pydantic import BaseModel, Field
import yaml
from yaml.loader import SafeLoader

import chainlit as cl
import jwt

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


# ===================================================================
# 【ヘッダーによる認証・認可】

def extract_access_token(cookie_header):
    """
    Cookieヘッダー文字列からaccess_tokenを抽出します。

    Args:
        cookie_header: Cookieヘッダー文字列

    Returns:
        access_tokenの値。見つからない場合はNoneを返します。
    """
    if not cookie_header:
        return None

    cookies = cookie_header.split(';')
    for cookie in cookies:
        cookie = cookie.strip()
        if cookie.startswith('access_token='):
            return cookie.split('=')[1]

    return None



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


# ヘッダー認証は、ヘッダーを使用してユーザーを認証する簡単な方法です。通常、リバース プロキシに認証を委任するために使用されます。
@cl.header_auth_callback
def header_auth_callback(headers: Dict) -> Optional[cl.User]:

    # Cookieヘッダーからaccess_tokenを抽出（Cookieヘッダーに refresh_token も入っていたので refresh_token も取り出すことは可能）
    cookie_header = headers.get('Cookie', '') or headers.get('cookie', '')
    access_token = extract_access_token(cookie_header)


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



    try:
        # JWTトークンをデコードして検証
        payload = jwt.decode(
            access_token, 
            SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            audience="authenticated",                   # Supabaseのデフォルトは authenticated 。確認方法：Authentication ページ > Users で登録ユーザーが見える。アプリケーションにログインしているユーザーのレコードの一番右側の「…」をクリック > View user info でユーザー情報を確認できる
            options={"verify_iat": True, "leeway": 30}  # 30秒のleewayを追加。トークンの発行時刻（iat）の検証時に30秒の誤差を許容
        )
        user_id = payload.get("email", "user")   # デフォルトを"user"に設定。Chainlit の画面で表示されるユーザーのこと。
        role = payload.get("role", "user")       # デフォルトロールを"user"に設定。Supabase のデフォルトは authenticated 。
        return cl.User(
            identifier=user_id,
            metadata={"role": role, "provider": "header"}
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
        print(f"認証中に予期せぬエラーが発生しました: {e}")
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