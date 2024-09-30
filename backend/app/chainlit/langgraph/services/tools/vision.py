import base64
import os
import requests

from typing import Sequence
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser


system_prompt = "あなたはベテランの絵の先生です。あなたに求められるのは、絵を完全再現するための文章を生成することです。提供された画像を次の観点で詳細かつハイレベルにレビューしてください。テーマ性、 構図、 光、 テクスチャ、粗密、 デッサン、遠近法、絵のスタイル、全体バランスについて解説し、絵を完全再現するための文章にまとめてください。"


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


@tool
async def vision(prompt: str, image_paths: Sequence[str]) -> str:
    """Pass multiple images to a multimodal AI to get a description of the images."""

    # 不適切な画像を入力すると生成が途中で止まる
    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro-002",
                                    temperature=1,
                                    streaming=False)   # 現状の実装では、ここは False でも True でも同じ挙動になる。ストリーミングの実装にはなっていないので False にしておく

    content = [{"type": "text", "text": prompt}]

    # Gemini は 16 枚まで同時に入力できる
    for image_path in image_paths:
        base64_image = encode_image(image_path)
        image_url = f"data:image/png;base64,{base64_image}"
        content.append({"type": "image_url", "image_url": image_url})


    message = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=content)
        ]


    output_parser = StrOutputParser()


    chain = model | output_parser


    # 0msys さんの実装だとストリーミングにはならない。最終的な表示はストリーミングっぽく見えけど、Vision モデルの結果はストリーミングでは返ってこない
    response = chain.invoke(message)

    
    # チャンクでリターンするのではなく、レスポンスが完成してからリターンしているので、ストリーミングではない
    # 特に問題はないのでこれは仕様と割り切っても良さそう
    return response


    # headers = {
    #     "Content-Type": "application/json",
    #     "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    # }

    # payload = {
    #     "model": "gpt-4o-2024-08-06",
    #     "messages": [
    #         {
    #             "role": "user",
    #             "content": [
    #                 {"type": "text", "text": prompt},
    #             ],
    #         }
    #     ],
    #     "max_tokens": 300,
    # }

    # for image_path in image_paths:
    #     base64_image = encode_image(image_path)
    #     payload["messages"][0]["content"].append(
    #         {
    #             "type": "image_url",
    #             "image_url": {
    #                 "url": f"data:image/jpeg;base64,{base64_image}",
    #                 "detail": "low",
    #             },
    #         }
    #     )

    # response = requests.post(
    #     "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
    # )

    # return response.json()["choices"][0]["message"]["content"]