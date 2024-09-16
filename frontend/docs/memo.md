- .cursorrules よりも Rules for AI の方が優先されてしまったため、削除した
- Rules for AI は YAML 形式で記載。コードを省略しないような制約条件も追加した。かなり強い影響を受けるので少し変えただけで結果が大きく変わる。今の設定でFIXする
- プロンプトは以下で実行する。Gemini 1.5 Pro か GPT-4o しかうまくいかない。Claude 3.5 は page.tsx だけ漏れたり、全くダメだったりして、ガチャ要素がある。XMLプロンプトじゃないせいかも。
```plaintext
@Codebase @setup-backend.md を実行してください。
```
- ★諸々修正したらコードベースのインデックスは作り直す
- 更新と実行では結果が異なる。更新はライブラリのインストールとかの案内はされない。
Claude 3.5 だと比較的うまくいくプロンプト(完璧ではない)
```plaintext
@Codebase @setup-backend.md を確認して私のコードテンプレートを更新してください。
```
- project_summary が自動的に読み込まれると結果が大きく変わるので .cursorignore で除外した
- セットアップ はやめたほうが良い。@setup-backend.md が指示書になっているため、実行して、が良さそう


