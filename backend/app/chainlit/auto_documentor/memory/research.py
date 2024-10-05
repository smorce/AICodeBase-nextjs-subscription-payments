from typing import TypedDict, List


# ★後で以下はファイル分割してモジュール化する
# from taskweaver.module.event_emitter import PostEventProxy
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
        """一時的に is_sequence の値を変更するメソッド"""
        original_value = self.is_sequence
        self.is_sequence = value
        try:
            yield
        finally:
            self.is_sequence = original_value



class ResearchState(TypedDict):
    task: dict
    initial_research: str
    sections: List[str]
    research_data: List[dict]
    # Report layout
    title: str
    headers: dict
    date: str
    table_of_contents: str
    introduction: str
    conclusion: str
    sources: List[str]
    report: str
    # [追加] PostProxyオブジェクト
    # LangGraph 内で扱いたいので追加した
    post_proxy: PostEventProxy


