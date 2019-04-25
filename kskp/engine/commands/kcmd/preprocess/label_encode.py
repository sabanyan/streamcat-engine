#!/usr/bin/env python3
# from kskp.engine.commands.kcmd.preprocess.common.preprocess import Preprocess
from common.preprocess import Preprocess
from sklearn.preprocessing import LabelBinarizer,LabelEncoder
import json
import sys
import argparse
import numpy as np
import pandas as pd
import pickle

class Label_encode(Preprocess):
    def __init__(self):
        super().__init__()
        self.name="label_encode"

    def label_encode_(self, df, col_name):
        """
		カテゴリ変数を連続値に変換する関数です。
		データセットと列名を受け取り、その列のクラスラベルを連続値に変換して
		データセットのもともとの列に置き換えます。
		返還後のデータセットと変換規則を返します。
		:param df: 学習に用いるデータセット
		:param col_name: one-hot化する列の列名
		"""
        le = LabelEncoder()
        le.fit(df[col_name])
        encoded=le.transform(df[col_name])
        df[col_name] = encoded

        #変換規則の登録
        self.enc_dict[col_name]=le

        return df


    def label_encode(self, data):
        """
		複数のカテゴリ変数をベクトル化して、それぞれ変換規則を保存する関数です。
		ベクトル化したデータセットを返します。
		変換規則はenc_dictに保存されています。

		:param data: 学習で用いるデータセット
		:param preprocessing_str:コマンドラインで入力され前処理に関する変数。('col_name1:le col_name2:lb'　の形式)
		"""
        if self.columns != None:
            self.enc_dict = {}#連続値用
            splited = self.columns.split(",")
            for spl in splited:
                data = self.label_encode_(data, spl)
        return data

    def make_parser(self):
        """
        parse_argsによって内部的に呼ばれる関数です。
        共通オプションを追加するsuper().make_parser()を実行した後、固有オプションを追加したパーサーを返します。
        """
        # 固有部分
        parser=super().make_parser()
        parser.add_argument("-c","--columns",dest="columns",help="select colums you wish to normalize",default=None,type=str)
        return parser


    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """

        self.columns=parsed.columns

    def parse_args(self,args):
        """
		コマンドライン引数をパースする関数です。
		すべてのオプションをパースしたものを返します。

		:param args: コマンドライン引数
		"""
        parser=self.make_parser()
        return parser.parse_args(args)

    def main(self,args):
        """
        メイン関数です
        受けたcsv形式のデータフレームに対して、指定された列のラベルエンコードを行います
        出力はラベルエンコード後のデータフレーム(csv形式)です
        また、変換規則に関するファイルlabel.jsonが生成されます
        上記ファイルをpredict.py実行時に指定してください
        """

        parsed=self.parse_args(args)

        self.set_parsed_args_common(parsed)
        self.set_parsed_args_unique(parsed)

        #入力ファイル読み込み
        data=pd.read_csv(self.input)

        #ラベルエンコード
        encoded=self.label_encode(data)

        #変換規則のファイル出力
        with open(self.temp_files_path.joinpath("label.pickle"), "wb") as f:
            pickle.dump(self.enc_dict,f)

        #前処理の順番を保存
        self.write_order()

        #エンコード後のデータセットの出力
        encoded.to_csv(self.output,index=False)
        # return encoded

if __name__=="__main__":
    label_enc=Label_encode()
    label_enc.main(sys.argv[1:])
