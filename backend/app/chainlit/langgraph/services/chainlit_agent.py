import chainlit as cl
from zoneinfo import ZoneInfo

from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
from chainlit.input_widget import Select, Switch

from services.agent import SingleAgent
# from services.voicevox import Voicevox
# from services.voicevox import SpeakerData


# VOICEVOX は使う予定がないのでコメントアウトした


class ChainlitAgent(SingleAgent):

    def __init__(
        self,
        system_prompt: str,
        speak: bool       = False,
        speaker_name: str = "四国めたん",
        style_name: str   = "ノーマル",
        dir_path: str     = "./",
    ):
        super().__init__(system_prompt=system_prompt)
        self.speak    = speak
        self.dir_path = dir_path
        # if speak:
        #     self.voicevox_service = Voicevox(
        #         speaker_name=speaker_name, style_name=style_name, dir_path=dir_path
        #     )

    async def on_chat_start(self):
        """
        チャットが開始されたときに呼び出される関数
        """
        # Settingsの初期値を設定
        settings = await cl.ChatSettings(
            [
                Switch(
                    id="Speak",
                    label="読み上げ",
                    initial=False,
                    description="読み上げを行うか選択してください。",
                ),
                Select(
                    id="Speaker_ID",
                    label="VOICEVOX - Speaker Name and Style",
                    # items=SpeakerData().get_all_speaker_and_style_dict(),
                    items={"speaker - style": "ダミースタイル"},
                    initial_value="2",
                    description="読み上げに使用するキャラクターとスタイルを選択してください。",
                ),
            ]
        ).send()
        # Settingsの初期値を元に、設定を更新
        await self.on_settings_update(settings)

    async def on_settings_update(self, settings: dict):
        """
        Settingsが更新されたときに呼び出される関数
        """
        # Settingsの値を取得し、VOICEVOXの設定を更新
        self.speak = settings["Speak"]
        # self.voicevox_service = Voicevox(
        #     speaker_id=settings["Speaker_ID"], dir_path=self.dir_path
        # )

    async def on_message(self, msg: cl.Message, inputs: list):
        """
        メッセージが送信されたときに呼び出される関数
        """

        content = msg.content

        # 添付ファイルの情報を取得
        attachment_file_text = ""

        for element in msg.elements:
            attachment_file_text += f'- {element.name} (path: {element.path.replace("/workspace", ".")})\n'  # agentが参照するときは./files/***/***.pngのようになるので、それに合わせる

        if attachment_file_text:
            content += f"\n\n添付ファイル\n{attachment_file_text}"

        # 　現在の日時を取得(JST)
        now = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S %Z")

        content += f"\n\n(入力日時: {now})"

        # ユーザーのメッセージを履歴に追加
        inputs.append(HumanMessage(content=content))

        # メッセージインスタンスの作成
        res = cl.Message(content="")
        steps = {}
        async for output in self.astream_events(inputs):
            if output["kind"] == "on_chat_model_stream":
                await res.stream_token(output["content"])
            elif output["kind"] == "on_tool_start":
                async with cl.Step(name=output["tool_name"], type="tool") as step:
                    step.input = output["tool_input"]
                    steps[output["run_id"]] = step
            elif output["kind"] == "on_tool_end":
                step = steps[output["run_id"]]
                step.output = output["tool_output"]
                await step.update()

        await res.send()

        # 読み上げが有効な場合、読み上げファイルを生成し、メッセージに追加
        if self.speak:
            # file_path = self.voicevox_service.post_synthesis_returned_in_file(
            #     text=res.content, use_manuscript=True, file_name="読み上げ"
            # )

            # ダミーのファイルパス
            file_path = "./.files/ダミー.wav"
            elements = [
                cl.Audio(
                    name="音声を読み上げます", path=file_path, display="inline", auto_play=True
                ),
            ]
            res.elements = elements
            await res.update()

        return AIMessage(content=res.content)
