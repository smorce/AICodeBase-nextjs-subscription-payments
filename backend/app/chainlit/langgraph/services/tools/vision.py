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

    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro-002",
                                    temperature=1,
                                    streaming=True)    # ココを False にすると続きが生成されない

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


    response = chain.invoke(message)


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