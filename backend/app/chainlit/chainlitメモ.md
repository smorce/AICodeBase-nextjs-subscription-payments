## Stepクラスの実装方法
- スタートやクローズを意識しなくても良い方法
    - async with cl.Step(name="", type="llm", root=True) as root_step:
    - @cl.step(name="", type="llm", root=True)
        - current_step = cl.context.current_step
- 自分でスタートやクローズを書く方法
    - cur_step = cl.Step(name="aaa", type="llm", root=False)    # ステップインスタンス作成
    - cl.run_sync(cur_step.__aenter__())                        # ステップ開始
    - content = format_post_body( content )                     # コンテンツのフォーマット
    - cl.run_sync(cur_step.stream_token(content, True))         # ★画面に表示。このタイミングで表示することで make_async が消えずに残る
    - cl.run_sync(cur_step.update())                            # ステップのアップデート（確か、四角の中の表示が変わった気がする）
    - cl.run_sync(cur_step.__aexit__(None, None, None))         # ステップ終了(閉じる)
    - cur_step = None                                           # TaskWeaver では None でリセットしていたので一応やる



## TaskWeaver
今だと、「トークンが生成される ＝ イベント」を定義しているので、
トークンが生成されるたびに StreamHandler が呼び出されるようになっている。
あとは、StreamHandler 内で run_sync(stream_token()) すれば TaskWeaver っぽくなるはず。

def StreamHandler(~~~):
    print("トークンが生成されました")
    cur_step = cl.Step(name="aaa", type="llm", root=False)    # ステップインスタンス作成
    cl.run_sync(cur_step.__aenter__())                        # ステップ開始
    content = format_post_body( content )                     # コンテンツのフォーマット
    cl.run_sync(cur_step.stream_token(content, True))         # ★画面に表示。このタイミングで表示することで make_async が消えずに残る
    cl.run_sync(cur_step.update())                            # ステップのアップデート（確か、四角の中の表示が変わった気がする）
    cl.run_sync(cur_step.__aexit__(None, None, None))         # ステップ終了(閉じる)
    cur_step = None                                           # TaskWeaver では None でリセットしていたので一応やる


TaskWeaver では
- Agent が起動して処理開始（__aenter__）
- 諸々の処理中に、各種イベントが発火することがある。イベントが発火する度にイベントに応じた処理をして、コンテンツを stream_token する。
- 諸々の処理が終わって、メッセージのアップデートをする。この時に最後の処理結果が stream_token され、その後に cl.run_sync(cur_step.update()) が実行される。（四角の中の表示が変わる？）
- 最後に閉じる（__aexit__）。このタイミングでも stream_token され、画面に出力される。画面に出力される内容は メッセージのアップデート時と同じ内容の可能性があるので、stream_token するかは必要に応じて。



## make_async の使い方
make_async は同期関数 (func_A) を非同期で処理する。func_A の処理結果は表示されず、裏側で処理される

handle_post の中でイベントタイプごとに処理をわける。

↓中で handle_post が呼び出される
def post_proxy.update_send_to():
    handle_post(type=PostEventType.post_send_to_update, msg)

def post_proxy.post_attachment_update():
    handle_post(type=PostEventType.post_attachment_update, msg)

def func_A(input, event_emitter):
    post_proxy = event_emitter.create_post_proxy()  # コールバック関数のインスタンス作成
    post_proxy.update_send_to()                     # イベント発火

    time.sleep(5)
    print(input)
    result = "Hello!"

    post_proxy.update_message()           # イベント発火
    post_proxy.post_attachment_update()   # イベント発火
    post_proxy.end()                      # イベント発火
    
    return result


input  ="文字列"
answer = await cl.make_async(func_A)(
    input,            # func_A の引数をここに入力
    event_emitter
    )
await cl.Message(content=answer).send()    # ここで画面に表示しないと実行したことが分からなくなる




--------------------------
メモ：
・make_async で特定の処理(Func_A)をする。その際に、Func_A にはコールバック関数を仕込んでおく
・上記の Func_A の処理中にイベントが発火すると、コールバック関数が起動する
・コールバック関数には、複数のイベントタイプを仕込んでおく
　　イベント1(例えば post_attachment_update )がきたらXXXXする
　　　　# 一連の流れ
　　　　print("トークンが生成されました")
　　　　print("ここに特定の処理を記載")
　　　　cur_step = cl.Step(name="aaa", root=False)                      # ステップ インスタンス作成
　　　　cl.run_sync(cur_step.__aenter__())                                    # ステップ開始
　　　　content = format_post_body( content )                               # コンテンツのフォーマット
　　　　cl.run_sync(cur_step.stream_token(content, True))            # ★画面に表示。このタイミングで表示することで make_async が消えずに残る
　　　　cl.run_sync(cur_step.update())                                           # ステップのアップデート（確か、四角の中の表示が変わった気がする）
　　　　cl.run_sync(cur_step.__aexit__(None, None, None))         # ステップ終了(閉じる)
　　　　cur_step = None                                                                  # TaskWeaver では None でリセットしていたので一応やる
　　イベント2がきたらXXXXする
　　イベント3がきたらXXXXする
・make_async は処理が終了すると消えるので、★のタイミングで cl.run_sync することで結果の表示を消えないように残す



  