# 全てのディレクトリに__init__.pyファイルを配置し、以下をやらないと絶対インポートでモジュールを読み込むことができなかった

import sys
import os

def setup_paths():
    # 現在のファイルのディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # プロジェクトのルートディレクトリを計算
    project_root = os.path.abspath(os.path.join(current_dir, "../../.."))

    # ルートディレクトリをsys.pathの先頭に追加
    sys.path.insert(0, project_root)