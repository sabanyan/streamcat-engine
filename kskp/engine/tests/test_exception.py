"""
例外処理が正しく行われるかどうかのテスト
"""

import unittest

def do_something(first_pow):
    i = 0
    for n in range(2 ** first_pow):
        i += n
    # try:
    #     i = i / 0
    # except Exception as e:
    #     ex =  ValueError(f'first_pow: {first_pow}')
    #     ex.__cause__ = e
    #     return ex
    return i

class ErrorHandlingTestCase(unittest.TestCase):
    def test_concurrent_errors(self):
        """
        エラーを並列で発生させられるかどうかのテスト
        (multiprocess)
        """
        from concurrent.futures import ProcessPoolExecutor, as_completed

        with ProcessPoolExecutor() as executor:
            # 並行処理する対象とそれに対応する値 (処理の引数) を辞書で用意する
            mappings = {executor.submit(do_something, n): n for n in [28, 26, 24, 22]}

            # futures.as_completed() は処理がおわったものから結果を返していくジェネレータ
            for future in as_completed(mappings):
                # 完了した処理に対応する引数を辞書から取得する
                target = mappings[future]
                # 処理結果を取得する
                result = future.result()
                # 結果を表示する
                msg = '{n}: {prime}'.format(n=target, prime=result)
                print(msg)

    def test_websocket(self):
        """
        websocketの動作確認
        """
