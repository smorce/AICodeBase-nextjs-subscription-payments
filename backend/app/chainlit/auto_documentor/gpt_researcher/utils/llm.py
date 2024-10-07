# libraries
from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from colorama import Fore, Style
from fastapi import WebSocket
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from gpt_researcher.master.prompts import auto_agent_instructions, generate_subtopics_prompt

from .validators import Subtopics

def get_provider(llm_provider):
    match llm_provider:
        case "openai":
            from ..llm_provider import OpenAIProvider
            llm_provider = OpenAIProvider
        case "azureopenai":
            from ..llm_provider import AzureOpenAIProvider
            llm_provider = AzureOpenAIProvider
        case "google":
            from ..llm_provider import GoogleProvider
            llm_provider = GoogleProvider
        case "openrouter":
            from ..llm_provider import OpenRouterProvider
            llm_provider = OpenRouterProvider

        case _:
            raise Exception("LLM provider not found.")

    return llm_provider


async def create_chat_completion(
        messages: list,  # type: ignore
        model: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,    # 出力するトークン数の最大値。入力+出力 のトークン数ではない。
        llm_provider: Optional[str] = None,
        stream: Optional[bool] = False,
        websocket: WebSocket | None = None,
) -> str:
    """Create a chat completion using the OpenAI API
    Args:
        messages (list[dict[str, str]]): The messages to send to the chat completion
        model (str, optional): The model to use. Defaults to None.
        temperature (float, optional): The temperature to use. Defaults to 0.9.
        max_tokens (int, optional): The max tokens to use. Defaults to None.
        stream (bool, optional): Whether to stream the response. Defaults to False.
        llm_provider (str, optional): The LLM Provider to use.
        webocket (WebSocket): The websocket used in the currect request
    Returns:
        str: The response from the chat completion
    """

    # validate input
    if model is None:
        raise ValueError("Model cannot be None")
    if model == "gemini-1.5-flash-002" or model == "gemini-1.5-pro-002":
        if max_tokens is not None and max_tokens > 8001:                   # flash も pro も 出力トークンの最大値は約 8000 で共通
            raise ValueError(
                f"Max tokens cannot be more than 8001, but got {max_tokens}")

    # Get the provider from supported providers
    ProviderClass = get_provider(llm_provider)
    provider = ProviderClass(
        model,
        temperature,
        max_tokens
    )

    # create response
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            print("auto_documentor/utils/llms.py: 10回チャレンジします")
            response = await provider.get_chat_response(messages, stream, websocket)
            # Check if the response is valid. Add specific checks based on your needs.
            # For example, check if the response is not empty, has the expected format, etc.
            if response:  # Replace with your validation logic
                return response
            else:
                logging.warning(f"Invalid response received on attempt {attempt + 1}. Retrying...")
        except Exception as e:
            logging.error(f"Error on attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                logging.info("Retrying...")
                # Consider adding a small delay before retrying to avoid overwhelming the API
                await asyncio.sleep(1)  # Wait for 1 second
            else:
                raise  # Re-raise the exception after all attempts have failed

    logging.error("Failed to get a valid response after multiple attempts.")
    raise RuntimeError("Failed to get a valid response after multiple attempts.")


def choose_agent(smart_llm_model: str, llm_provider: str, task: str) -> dict:
    """Determines what server should be used
    Args:
        task (str): The research question the user asked
        smart_llm_model (str): the llm model to be used
        llm_provider (str): the llm provider used
    Returns:
        server - The server that will be used
        agent_role_prompt (str): The prompt for the server
    """
    try:
        response = create_chat_completion(
            model=smart_llm_model,
            messages=[
                {"role": "system", "content": f"{auto_agent_instructions()}"},
                {"role": "user", "content": f"task: {task}"}],
            temperature=0,
            llm_provider=llm_provider
        )
        agent_dict = json.loads(response)
        print(f"Agent: {agent_dict.get('server')}")
        return agent_dict
    except Exception as e:
        print(f"{Fore.RED}Error in choose_agent: {e}{Style.RESET_ALL}")
        return {"server": "Default Agent",
                "agent_role_prompt": "You are an AI critical thinker research assistant. Your sole purpose is to write well written, critically acclaimed, objective and structured reports on given text."}


async def construct_subtopics(task: str, data: str, config, subtopics: list = []) -> list:
    try:
        parser = PydanticOutputParser(pydantic_object=Subtopics)

        prompt = PromptTemplate(
            template=generate_subtopics_prompt(),
            input_variables=["task", "data", "subtopics", "max_subtopics"],
            partial_variables={
                "format_instructions": parser.get_format_instructions()},
        )

        print(f"\n🤖 Calling {config.smart_llm_model}...\n")

        if config.llm_provider == "openai":
            model = ChatOpenAI(model=config.smart_llm_model)
        elif config.llm_provider == "azureopenai":
            from langchain_openai import AzureChatOpenAI
            model = AzureChatOpenAI(model=config.smart_llm_model)
        else:
            return []

        chain = prompt | model | parser

        output = chain.invoke({
            "task": task,
            "data": data,
            "subtopics": subtopics,
            "max_subtopics": config.max_subtopics
        })

        return output

    except Exception as e:
        print("Exception in parsing subtopics : ", e)
        return subtopics