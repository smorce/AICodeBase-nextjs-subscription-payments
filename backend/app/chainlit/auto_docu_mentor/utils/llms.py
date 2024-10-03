from langchain.adapters.openai import convert_openai_messages
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

import os
from typing import Optional
# pip install pyyaml
# import yaml

# 現在のスクリプトのディレクトリを取得
# current_dir = os.getcwd()

# 一つ上のディレクトリにあるweb_search_config.yamlのパスを作成
# config_path = os.path.join(current_dir, '..', 'web_search_config.yaml')

# YAMLファイルを読み込む（使っていないが残しておく）
# with open(config_path, 'r') as file:
#     config = yaml.safe_load(file)

# OpenRouter にする
class ChatOpenRouter(ChatOpenAI):
    openai_api_base: str
    openai_api_key: str
    model_name: str

    def __init__(self,
                 model_name: str,
                 openai_api_key: Optional[str] = None,
                 openai_api_base: str = "https://openrouter.ai/api/v1",
                 model_kwargs: Optional[dict] = None,
                 **kwargs):
        # openai_api_key = openai_api_key or config.get('openrouter_api_key')
        # web_search_config.yaml から読み込むようにしていたが、環境変数から読み込むように変更
        openai_api_key = openai_api_key or os.getenv("OPENROUTER_API_KEY")

        # `model_kwargs`を`kwargs`に追加
        if model_kwargs:
            kwargs['model_kwargs'] = model_kwargs

        super().__init__(openai_api_base=openai_api_base,
                        openai_api_key=openai_api_key,
                        model_name=model_name, **kwargs)


def call_model(prompt: list, model: str, max_retries: int = 2, response_format: str = None) -> str:

    model_kwargs = {}
    if response_format == 'json':
        model_kwargs["response_format"] = {"type": "json_object"}     # JSON モード。★ ChatGoogleGenerativeAI に変えたけど、Gemini は JSON モードをサポートしていない。一旦やってみて JSON パースに失敗するなら元に戻す。Gemini の性能が高ければ JSON モードが使えなくても良い感じに JSON で返してくれるはず。

    lc_messages = convert_openai_messages(prompt)
    # response = ChatOpenAI(model=model, max_retries=max_retries, model_kwargs=optional_params).invoke(lc_messages).content

    # LCEL の書き方にする
    # llm = ChatOpenAI(model=model, max_retries=max_retries, model_kwargs=optional_params)

    # OpenRouter にする。これはリサーチャー以外のマルチエージェントが使うモデル。以下は task.json の値
    # model: "openai/gpt-4o"
    # model: "openai/gpt-3.5-turbo-0125"  # 16k
    # model: "google/gemini-flash-1.5"    # 本家APIじゃないので有料だけど一旦これで。ただし、ChatGoogleGenerativeAI を使えば本家APIを使える。
    # model: "anthropic/claude-3-haiku"
    # llm = ChatOpenRouter(model_name=model, max_retries=max_retries, model_kwargs=model_kwargs)
    llm = ChatGoogleGenerativeAI(model=model, max_retries=max_retries, model_kwargs=model_kwargs)

    system_prompt = "あなたはとても賢いAIアシスタントです。"
    message = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=lc_messages)
        ]

    # 「StrOutputParser」は、文字列として出力するパーサーです。
    parser = StrOutputParser()

    chain = llm | parser

    response = chain.invoke(message)

    return response