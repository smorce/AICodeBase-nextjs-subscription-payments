from utils.file_formats import \
    write_to_file, \
    write_md_to_pdf, \
    write_md_to_word, \
    write_text_to_md, \
    split_text_into_chunks
from utils.views import print_agent_output
from utils.llms import call_model
import asyncio


class PublisherAgent:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    async def publish_research_report(self, research_state: dict, publish_formats: dict):
        layout = self.generate_layout(research_state)
        # 英語コンテンツを保存する
        await write_to_file(os.path.join(self.output_dir, 'en_content.md'), layout)

        # ------------------------------------------------
        # コンテンツを日本語訳する
        # ------------------------------------------------
        # コンテンツを6000文字以下に区切る
        chunks = split_text_into_chunks(layout)
        # コンテンツを日本語に翻訳する
        task  = research_state.get("task")
        model = task.get("model")

        async def translate_chunk(chunk: str, model: str) -> str:
            """
            チャンクを日本語に翻訳する非同期関数。

            Args:
                chunk (str): 翻訳対象のテキストチャンク。
                model (str): 使用する言語モデル。

            Returns:
                str: 翻訳されたテキスト。日本語の場合は None を返す。
            """
            prompt = [{
                "role": "system",
                "content": "あなたは与えられた文章を極めて自然な日本語に翻訳するプログラムです。翻訳した文章は省略せずに全文を出力してください。なお、文章が日本語だった場合は None だけ出力してください。"
            }, {
                "role": "user",
                "content": chunk
            }]
            response = call_model(prompt, model)
            return response

        # 並列処理でチャンクを翻訳
        try:
            tasks = [translate_chunk(chunk, model) for chunk in chunks]
            translated_chunks = await asyncio.gather(*tasks)
        except Exception as e:
            print(f"日本語翻訳でエラー(レートリミット制限など): {e}")

        # チャンクが空行から始まる場合、翻訳するとその空行が消えてしまうので、元のチャンクと比較して、元のチャンクが空行から始まり translated_chunks が空行から始まっていない場合は translated_chunks の冒頭に空行を追加する
        for i, (original_chunk, translated_chunk) in enumerate(zip(chunks, translated_chunks)):
            if original_chunk.startswith('\n') and not translated_chunk.startswith('\n'):
                translated_chunks[i] = '\n' + translated_chunk

        # 翻訳されたチャンクを結合
        if None not in translated_chunks:
            translated_layout = "".join(translated_chunks)
            layout = translated_layout
        else:
            pass  # None が含まれている場合は文章が日本語なので layout をそのまま使うため何もしない
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

## {headers.get("references")}
{references}
"""
        return layout

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