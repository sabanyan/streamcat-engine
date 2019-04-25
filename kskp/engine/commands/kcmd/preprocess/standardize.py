#!/usr/bin/env python3
import sys
import pickle

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from kskp.engine.commands.kcmd.preprocess.common.preprocess import Preprocess
# from common.preprocess import Preprocess

class Standardize(Preprocess):
    def __init__(self):
        super().__init__()
        self.name = 'standardize'

    def standardize(self, data):
        self.std_dict = {}

        if self.columns != None or self.all_columns:
            if self.all_columns:
                with open(self.temp_files_path + 'target_col_name.txt','r') as f:
                    target_col_name = f.read()
                columns = data.columns

                # ターゲット列の削除
                columns.remove(target_col_name)
            else:
                splited = self.columns.split(',')
                columns = splited

            for col_name in columns:
                col = data[col_name].values.reshape((-1, 1))
                sc = StandardScaler()
                sc.fit(col)
                array = np.array(sc.transform(col)).reshape((-1, 1))
                data[col_name] = pd.DataFrame(array, columns=[col_name])
                self.std_dict[col_name] = sc

        return data

    def make_parser(self):
        """
        parse_argsによって内部的に呼ばれる関数です。
        共通オプションを追加するsuper().make_parser()を実行した後、固有オプションを追加したパーサーを返します。
        """

        # 固有部分
        parser = super().make_parser()
        parser.add_argument('-c', '--columns', dest='columns', help='select colums you wish to normalize', default=None, type=str)
        parser.add_argument('-a', '--all_columns', dest='all_columns', default=False,action='store_const', const=True)
        return parser

    def set_parsed_args_unique(self, parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """

        self.columns = parsed.columns
        self.all_columns = parsed.all_columns

    def parse_args(self, args):
        """
        コマンドライン引数をパースする関数です。
        すべてのオプションをパースしたものを返します。

        :param args: コマンドライン引数
        """
        parser = self.make_parser()
        return parser.parse_args(args)

    def main(self, args):
        """
        メイン関数です
        受けたcsv形式のデータフレームに対して、指定された列の標準化を行います
        出力は標準化後のデータフレーム(csv形式)です
        """
        parsed = self.parse_args(args)

        self.set_parsed_args_common(parsed)
        self.set_parsed_args_unique(parsed)

        #入力ファイル読み込み
        data = pd.read_csv(self.input)

        #標準化
        standardized = self.standardize(data)

        #変換規則のファイル出力
        with open(self.temp_files_path.joinpath('standardize.pickle'), 'wb') as f:
            pickle.dump(self.std_dict, f)

        #前処理の順番を保存
        self.write_order()

        # return standardized

        # #標準化後のデータセット出力
        standardized.to_csv(self.output, index=False)

if __name__ == '__main__':
    std = Standardize()
    std.main(sys.argv[1:])
