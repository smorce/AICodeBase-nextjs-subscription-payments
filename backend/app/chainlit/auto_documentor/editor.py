from datetime import datetime
from utils.views import print_agent_output
from utils.llms import call_model
from memory.draft import DraftState
from langgraph.graph import StateGraph, END
import asyncio
import json
import re
import chainlit as cl

from path_setup import setup_paths
setup_paths()

try:
    # 絶対インポートする
    # どうやっても相対インポートが無理だった。Dockerファイルでパスを通したりしないとダメか？
    from app.chainlit.auto_documentor.researcher import ResearchAgent
    from app.chainlit.auto_documentor.reviewer import ReviewerAgent
    from app.chainlit.auto_documentor.reviser import ReviserAgent
except ImportError as e:
    print(f"必要なライブラリをインポートできませんでした: {e}")
    import sys
    sys.exit(1)

class EditorAgent:
    def __init__(self, task: dict):
        self.task = task

    def plan_research(self, research_state: dict):
        """
        Curate relevant sources for a query
        :param summary_report:
        :return:
        :param total_sub_headers:
        """

        initial_research = research_state.get("initial_research")
        post_proxy       = research_state.get("post_proxy")
        max_sections     = self.task.get("max_sections")

        post_proxy.update_status("[doing]EditorAgent✍🏻: 初期調査に基づいてレポートの概要と構成を計画する")

        prompt = [{
            "role": "system",
            "content": "You are a research director. Your goal is to oversee the research project"
                       " from inception to completion.\n "
        }, {
            "role": "user",
            "content": f"Today's date is {datetime.now().strftime('%d/%m/%Y')}\n."
                       f"Research summary report: '{initial_research}'\n\n"
                       f"Your task is to generate an outline of sections headers for the research project"
                       f" based on the research summary report above.\n"
                       f"You must generate a maximum of {max_sections} section headers.\n"
                       f"You must focus ONLY on related research topics for subheaders and do NOT include introduction, conclusion and references.\n"
                       f"You must return nothing but a JSON with the fields 'title' (str) and "
                       f"'sections' (maximum {max_sections} section headers) with the following structure: "
                       f"'{{title: string research title, date: today's date, "
                       f"sections: ['section header 1', 'section header 2', 'section header 3' ...]}}.\n "
        }]

        print_agent_output(f"Planning an outline layout based on initial research...", agent="EDITOR")
        response = call_model(prompt=prompt, model=self.task.get("model"), response_format="json")
        # print("デバッグ。JSON形式か？ Gemini は JSON モードをサポートしていないので、ココがあやしい。response ↓")
        # print(response)
        # → Gemini は JSON モードをサポートしていないけど {"type": "json_object"} を指定してもエラーにならないし、ちゃんと JSON データで返してきたので問題なし

        # 正規表現を使って{}の中身を抽出する
        match = re.search(r'\{.*\}', response, re.DOTALL)

        if match:
            json_str = match.group(0)
            # JSONをパースしてPythonの辞書型に変換する
            plan = json.loads(json_str)
            print(plan)
        else:
            print("plan_research: JSON形式のデータが見つかりませんでした。")

        post_proxy.update_status("[done]EditorAgent✍🏻: 初期調査に基づいてレポートの概要と構成を計画する")

        return {
            "title": plan.get("title"),
            "date": plan.get("date"),
            "sections": plan.get("sections"),
            "post_proxy": post_proxy,
        }

    async def run_parallel_research(self, research_state: dict):
        """サブグラフを並列かつ独立して動かす"""
        # --------------------------------------------
        # サブグラフで動かすエージェント3つ
        ##### 研究者 (gpt-researcher) - サブトピックについて詳細な調査を行い、草稿を書きます。
        ##### レビュー担当者           - follow_guidelines に基づいて下書きの正確性を検証し、フィードバックを提供します。
        ##### 校閲者                  - レビュー担当者のフィードバックに基づいて満足のいく内容になるまで下書きを修正します。
        # --------------------------------------------
        research_agent = ResearchAgent()
        reviewer_agent = ReviewerAgent()
        reviser_agent  = ReviserAgent()
        # --------------------------------------------
        queries = research_state.get("sections")           # サブトピック(アウトライントピック)のリスト。ちゃんと3つになっていた
        title = research_state.get("title")                # これは初期計画及びレポートのタイトルになる
        post_proxy = research_state.get("post_proxy")

        post_proxy.progress(f"デバッグ サブトピック(アウトライントピック)のリスト: {queries}\n")


        post_proxy.update_status("[doing]ResearchAgent🔎 & ReviewerAgent📑 & ReviserAgent📜: 各アウトライントピックについて並行してリサーチする")


        # 進捗表示（使うかもしれないので残しておく）
        # progress_updated = 0
        # total_progress = len(queries)
        # # 進捗パーセントを計算（初回は10%から始める）
        # progress_percentage = 10
        # # 進捗バーを作成
        # progress_bar = '█' * progress_updated + '░' * (total_progress - progress_updated)
        # # 進捗バーとパーセントを組み合わせた文字列を作成
        # progress_string = f'全体の進捗(目安): {progress_bar} {progress_percentage}%'
        # # post_proxy.progress(progress_string)


        # 各エージェントの処理をラップする関数を定義
        async def researcher_with_print(state):
            # nonlocal progress_updated, total_progress
            post_proxy.update_status("[doing]░░░░░ResearchAgent🔎: アウトライントピックを並列リサーチする")
            result = await research_agent.run_depth_research(state)
            # post_proxy.update_status メソッドは並列処理を考慮していないので順番がぐちゃぐちゃになると表示がおかしくなるため、update_message メソッドで強制的に上書きする
            post_proxy.update_message(
                                    "[doing]░░░░░ResearchAgent🔎: アウトライントピックを並列リサーチする",
                                    "[done]░░░░░ResearchAgent🔎: アウトライントピックを並列リサーチする",
                                    False
                                    )
            # progress_updated += 1
            # # 進捗パーセントを計算
            # progress_percentage = int((progress_updated / total_progress) * 100)
            # # 進捗バーを作成
            # progress_bar = '█' * progress_updated + '░' * (total_progress - progress_updated)
            # # 進捗バーとパーセントを組み合わせた文字列を作成
            # progress_string = f'全体の進捗(目安): {progress_bar} {progress_percentage}%'
            # post_proxy.prev_content_delete()
            # post_proxy.progress(progress_string)
            return result

        def reviewer_with_print(state):
            # nonlocal a
            # task.json でガイドラインが False ならレビュー結果は None になる
            post_proxy.update_status("[doing]░░░░░ReviewerAgent📑: レビューをする")
            result = reviewer_agent.run(state)
            post_proxy.update_message(
                                    "[doing]░░░░░ReviewerAgent📑: レビューをする",
                                    "[done]░░░░░ReviewerAgent📑: レビューをする",
                                    False
                                    )
            return result

        def reviser_with_print(state):
            # reviewer の結果が None なら 校閲者 は呼び出されない
            post_proxy.update_status("[doing]░░░░░ReviserAgent📜: 校正する")
            result = reviser_agent.run(state)
            post_proxy.update_message(
                                    "[doing]░░░░░ReviserAgent📜: 校正する",
                                    "[done]░░░░░ReviserAgent📜: 校正する",
                                    False
                                    )
            return result



        # ワークフローを定義
        workflow = StateGraph(DraftState)

        # ラップした関数をノードとして追加
        workflow.add_node("researcher", researcher_with_print)
        workflow.add_node("reviewer", reviewer_with_print)
        workflow.add_node("reviser", reviser_with_print)

        # set up edges researcher->reviewer->reviser->reviewer...
        workflow.set_entry_point("researcher")
        workflow.add_edge('researcher', 'reviewer')
        workflow.add_edge('reviser', 'reviewer')      # ループバック
        # 条件付きエッジ。レビュー担当者によるレビューメモが存在する場合、グラフは修正担当者に指示されます。そうでない場合、サイクルは最終草案で終了します。
        workflow.add_conditional_edges('reviewer',
                                        (lambda draft: "accept" if draft['review'] is None else "revise"),
                                        {"accept": END, "revise": "reviser"})

        chain = workflow.compile()

        # Execute the graph for each query in parallel
        print_agent_output(f"Running the following research tasks in parallel: {queries}...", agent="EDITOR")
        # ainvoke なので複数のクエリーに対して非同期かつ並列で実行。各アウトライン トピックについて並行して実行する
        final_drafts = [chain.ainvoke({"task": research_state.get("task"), "topic": query, "title": title})
                        for query in queries]
        # asyncio.gather なので全部のタスクが終了するまで次には行かない
        research_results = [result['draft'] for result in await asyncio.gather(*final_drafts)]


        # update_status が使えない理由は以下
        # 各エージェントの処理をラップする関数を定義して、そこで post_proxy.update_status() しているため、self.prev_content がガンガン更新されてしまい、「[doing]ResearchAgent ~~~ してリサーチする」 とは違う内容になっているから
        # → 強制的にメッセージをアップデートするメソッドを使う
        post_proxy.update_message(
                                "[doing]ResearchAgent🔎 & ReviewerAgent📑 & ReviserAgent📜: 各アウトライントピックについて並行してリサーチする",
                                "[done]ResearchAgent🔎 & ReviewerAgent📑 & ReviserAgent📜: 各アウトライントピックについて並行してリサーチする",
                                False
                                )


        # リターンするときに、ResearchState に対応する Kye の Value が更新される
        return {"research_data": research_results, "post_proxy":post_proxy}
