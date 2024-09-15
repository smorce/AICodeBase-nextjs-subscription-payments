# Supabase クライアントの設定:
# 環境変数から SUPABASE_URL と SUPABASE_KEY をロードし、Supabase クライアントを作成しました。
# これにより、アクセストークンの検証に必要な情報を取得します。
# アクセストークンの検証関数 verify_access_token の追加:
# verify_access_token 関数を追加し、アクセストークンをデコードおよび検証します。
# トークンが有効であれば、対応する UserInfo オブジェクトを返します。無効な場合は None を返します。
# JWT のデコードには pyjwt ライブラリを使用しています。必要に応じてライブラリをインストールしてください (pip install pyjwt)。
# カスタム認証コールバック auth_callback の修正:
# 認証リクエストから access_token を取得し、存在する場合は verify_access_token を使用してトークンを検証します。
# 有効なトークンが検証された場合、対応するユーザーとして認証を行います。
# アクセストークンが存在しない、または無効な場合は、従来のパスワード認証にフォールバックします。
# パスワード認証のフォールバックロジックの保持:
# 既存のパスワード認証ロジックを保持し、アクセストークンが提供されない場合に引き続き使用できるようにしました。
# チャット開始時のウェルカムメッセージの追加:
# on_chat_start 関数内でウェルカムメッセージをユーザーに送信します。
# メッセージ受信時のロジックの修正:
# カウンターの初期化に or 0 を追加し、初回実行時にエラーが発生しないようにしました。
# ai_message の生成部分にコメントを追加し、必要に応じてAIの返答ロジックを実装できるようにしました。
# 次のステップ:
# Chainlit 側の設定:
# Chainlit アプリケーションがクエリパラメータから access_token を受け取れるようになりました。
# ユーザーが Next.js アプリケーションからアクセスする際に、アクセストークンが適切に渡されることを確認してください。
# セキュリティの強化:
# アクセストークンの送信先が常に HTTPS で保護されていることを確認してください。
# トークンの有効期限やリフレッシュメカニズムを適切に設定し、セキュリティリスクを最小限に抑えてください。
# 依存関係のインストール:
# ★pyjwt ライブラリがインストールされていない場合は、以下のコマンドでインストールしてください。
# pip install pyjwt
# 環境変数の設定:
# ★.env ファイルに SUPABASE_URL と SUPABASE_KEY を正しく設定してください。
# Chainlit と Next.js の統合テスト:
# ウェブアプリケーションから Chainlit へのリダイレクト時に、アクセストークンが正しく渡され、シームレスなログインが実現されていることをテストしてください。
# これらの変更により、ユーザーがウェブアプリケーションから Chainlit に移行する際に再度ログインする必要がなくなり、シームレスなユーザー体験が提供されます。


★対応中。先にフロントエンドとバックエンドを分けた方が良いかも



import os
from dotenv import load_dotenv
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
from supabase import create_client, Client
import jwt

load_dotenv()

# 現在のディレクトリをこのファイルが存在するディレクトリに変更します
os.chdir(os.path.dirname(__file__))

# Supabaseの設定
SUPABASE_URL = os.getenv("SUPABASE_URL")　　設定する
SUPABASE_KEY = os.getenv("SUPABASE_KEY")　　設定する
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


# ===================================================================
# 【パスワードによる認証・認可】

AUTH_FILE_PATH = "config.yaml"

class UserInfo(BaseModel):
    """ログイン認証に使用するユーザー情報のスキーマ
    【登録情報】
      name: rine2
      email: rinerebox2@gmail.com
      password: test    ← これで UI に入力する
    """
    name: str = Field(
        description="登録されたユーザー名"
    )
    email: str = Field(
        description="登録されたemail"
    )
    password: str = Field(
        description="登録された、ハッシュ化済みパスワード"
    )

def verify_access_token(token: str):
    """アクセストークンの検証とユーザー情報の取得
    Args:
        token (str): アクセストークン
    Returns:
        UserInfo | None: 有効なトークンならUserInfo, それ以外はNone
    """
    try:
        # SupabaseのJWT設定に基づいてトークンをデコード
        payload = jwt.decode(token, SUPABASE_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or not email:
            return None
        # 必要に応じて追加のユーザー情報を取得
        # ここではメールアドレスのみ使用
        return UserInfo(name=email.split('@')[0], email=email, password="")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@cl.password_auth_callback
def auth_callback(request):
    """カスタム認証コールバック
    Args:
        request: Chainlitのリクエストオブジェクト
    Returns:
        cl.User | None
    """

    access_token = request.query_params.get("access_token")

    if access_token:
        user_info = verify_access_token(access_token)
        if user_info:
            return cl.User(
                identifier=user_info.name,
                metadata={"role": "user", "provider": "supabase_token"}
            )
        else:
            return None

    # パスワード認証にフォールバック
    # configファイルの存在確認と読み込み
    if os.path.isfile(AUTH_FILE_PATH):
        with open(AUTH_FILE_PATH) as file:
            config = yaml.load(file, Loader=SafeLoader)
    else:
        return None

    # 入力されたEmailアドレスと一致するユーザー情報をconfigから取得
    user_list = config.get("users",[])
    email = request.form.get("email")
    password = request.form.get("password")

    registered_user = [UserInfo(**user) for user in user_list if email == user.email]

    # 一致するユーザー情報がなければ失敗
    if len(registered_user) == 0:
        return None

    # ユーザー情報の取得
    registered_user = registered_user[0]
    registered_name = registered_user.name
    registered_email = registered_user.email
    registered_password = registered_user.password

    # 認証画面で入力されたパスワードのハッシュ化
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Emailとパスワードの比較
    if (email, hashed_password) == (registered_email, registered_password):
        # 認証成功
        return cl.User(
            identifier=registered_name, metadata={"role": "user", "provider": "credentials"}
        )
    else:
        # 認証失敗
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