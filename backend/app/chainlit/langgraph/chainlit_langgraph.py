import chainlit as cl
import os

from services.chainlit_agent import ChainlitAgent

# 以下は不要
# 現在のディレクトリをこのファイルが存在するディレクトリに変更します
# os.chdir(os.path.dirname(__file__))

# 現在のディレクトリ
# CURRENT_DIR = os.getcwd()

@cl.on_chat_start
async def on_chat_start():
    # フォルダを用意。毎回新しい id が振られる
    dir_path = f"./.files/{cl.user_session.get('id')}/"

    # print("★デバッグ")
    # print(dir_path)     #  ./.files/2c830ddb-b7f2-4649-9f08-01284184b1ef/


    os.makedirs(dir_path, exist_ok=True)
    system_prompt = "あなたは最高のアシスタントチャットボットです。どんな依頼にも丁寧に最高のサービスを提供します。"
    chainlit_agent = ChainlitAgent(
        system_prompt=system_prompt,
        dir_path=dir_path,
    )
    await chainlit_agent.on_chat_start()
    cl.user_session.set("chainlit_agent", chainlit_agent)


@cl.on_settings_update
async def on_settings_update(settings: dict):
    chainlit_agent = cl.user_session.get("chainlit_agent")
    await chainlit_agent.on_settings_update(settings)
    cl.user_session.set("chainlit_agent", chainlit_agent)


@cl.on_message
async def main(message: cl.Message):

    inputs = cl.user_session.get("inputs", [])
    chainlit_agent = cl.user_session.get("chainlit_agent")

    output = await chainlit_agent.on_message(message, inputs)
    inputs.append(output)
    cl.user_session.set("inputs", inputs)



# このスクリプトが直接実行された場合の処理を記述します。
# スクリプトがモジュールとして他のファイルからインポートされたときには、このブロック内のコードが実行されないようにしています。
if __name__ == "__main__":
    # chainlitのコマンドラインインターフェースからrun_chainlitをインポート
    from chainlit.cli import run_chainlit

    # このファイルをchainlitアプリケーションとして起動する関数を呼び出します。
    # __file__は現在のスクリプトファイルの名前を指します。
    run_chainlit(__file__)