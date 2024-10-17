from utils.file_formats import \
    write_to_file, \
    write_md_to_pdf, \
    write_md_to_word, \
    write_text_to_md, \
    split_text_into_chunks
from utils.views import print_agent_output
from utils.llms import call_model
import os
import asyncio


class PublisherAgent:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    async def publish_research_report(self, research_state: dict, publish_formats: dict):
        layout, references = self.generate_layout(research_state)
        # 英語コンテンツを保存する
        await write_to_file(os.path.join(self.output_dir, 'en_content.md'), layout)
        # レファレンスを保存する
        await write_to_file(os.path.join(self.output_dir, 'en_references.md'), references)
        # 英語コンテンツ+レファレンスを保存する
        await write_to_file(os.path.join(self.output_dir, 'en_content_on_references.md'), layout + references)

        # ------------------------------------------------
        # コンテンツの言語を判定し、必要に応じて日本語に翻訳する
        # ------------------------------------------------
        task = research_state.get("task")
        model = task.get("model")

        def detect_language(text: str, model: str) -> str:
            """
            テキストの言語を検出する非同期関数。

            Args:
                text (str): 言語を検出するテキスト。
                model (str): 使用する言語モデル。

            Returns:
                str: 'japanese' または 'other'
            """
            prompt = [{
                "role": "system",
                "content": "与えられたテキストの言語を判定してください。日本語の場合は 'japanese'、それ以外の場合は 'other' と回答してください。"
            }, {
                "role": "user",
                "content": text[:1000]  # 最初の1000文字だけを使用
            }]
            response = call_model(prompt, model)
            return response.strip().lower()

        async def translate_to_japanese(text: str, model: str) -> str:
            """
            テキストを日本語に翻訳する非同期関数。

            Args:
                text (str): 翻訳対象のテキスト。
                model (str): 使用する言語モデル。

            Returns:
                str: 翻訳されたテキスト。
            """
            chunks: list = split_text_into_chunks(text)
            translated_chunks = []

            async def translate_chunk(chunk):
                try:
                    prompt = [{
                        "role": "system",
                        "content": "あなたは賢い翻訳プログラムです。与えられた文章を極めて自然な日本語に翻訳してください。翻訳だけ行い、翻訳した文章は省略せずに全文を出力してください。"
                    }, {
                        "role": "user",
                        "content": chunk
                    }]
                    # call_model 関数が同期関数であり、その結果として文字列を返すため、await を使用すると「オブジェクト 'str' は 'await' 式で使用できません」というエラーが発生する
                    # call_model を非同期で実行するために asyncio.to_thread を使用
                    response = await asyncio.to_thread(call_model, prompt, model)
                    return response
                except Exception as e:
                    print(f"日本語翻訳でエラー(チャンクが16個以上だった場合のレートリミット制限など): {e}")
                    return f"日本語翻訳でエラー(チャンクが16個以上だった場合のレートリミット制限など): {e}"

            try:
                translated_chunks = await asyncio.gather(*[translate_chunk(chunk) for chunk in chunks])
                # チャンクが空行から始まる場合、翻訳するとその空行が消えてしまうので、元のチャンクと比較して、元のチャンクが空行から始まり translated_chunks が空行から始まっていない場合は translated_chunks の冒頭に空行を追加する
                for i, (original_chunk, translated_chunk) in enumerate(zip(chunks, translated_chunks)):
                    if original_chunk.startswith('\n') and not translated_chunk.startswith('\n'):
                        translated_chunks[i] = '\n' + translated_chunk
                return ''.join(translated_chunks)
            except Exception as e:
                print(f"翻訳プロセス全体でエラーが発生しました: {e}")
                return f"翻訳プロセス全体でエラーが発生しました: {e}"


        # 言語を検出
        language = detect_language(layout, model)


        if language == 'japanese':
            print_agent_output("コンテンツは既に日本語です。翻訳をスキップします。", agent="PUBLISHER")
        else:
            print_agent_output("コンテンツを日本語に翻訳します...", agent="PUBLISHER")
            layout = await translate_to_japanese(layout, model)

        # ------------------------------------------------


        await self.write_report_by_formats(layout, publish_formats)

        return layout

    def generate_layout(self, research_state: dict):
        """マークダウンで返却"""
        sections = '\n\n'.join(f"{value}"
                                 for subheader in research_state.get("research_data")
                                 for key, value in subheader.items())
        references = '\n'.join(f"{reference}" for reference in research_state.get("sources"))
        headers = research_state.get("headers")
        layout = f"""# {headers.get('title')}
#### {headers.get("date")}: {research_state.get('date')}

## {headers.get("introduction")}
{research_state.get('introduction')}

## {headers.get("table_of_contents")}
{research_state.get('table_of_contents')}

{sections}

## {headers.get("conclusion")}
{research_state.get('conclusion')}

"""
        references = f"""
## {headers.get("references")}
{references}"""

        # 日本語訳では references はいらないので分割した
        return layout, references

    async def write_report_by_formats(self, layout: str, publish_formats: dict):
        if publish_formats.get("pdf"):
            await write_md_to_pdf(layout, self.output_dir)
        if publish_formats.get("docx"):
            await write_md_to_word(layout, self.output_dir)
        if publish_formats.get("markdown"):
            await write_text_to_md(layout, self.output_dir)

    async def run(self, research_state: dict):
        task = research_state.get("task")
        post_proxy = research_state.get("post_proxy")
        post_proxy.update_status("[doing]PublisherAgent📢: 最終レポートを PDF、Docx、Markdown のマルチフォーマットで作成する")
        publish_formats = task.get("publish_formats")
        print_agent_output(output="Publishing final research report based on retrieved data...", agent="PUBLISHER")
        final_research_report = await self.publish_research_report(research_state, publish_formats)
        post_proxy.update_status("[done]PublisherAgent📢: 最終レポートを PDF、Docx、Markdown のマルチフォーマットで作成する")
        
        return {"report": final_research_report, "post_proxy": post_proxy}