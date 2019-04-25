#!/usr/bin/env python3
from kskp.engine.commands.kcmd.preprocess.common.preprocess import Preprocess
# from common.preprocess import Preprocess
from sklearn.preprocessing import LabelBinarizer,LabelEncoder
import json
import sys
import argparse
import numpy as np
import pandas as pd
import pickle

class One_hot_encode(Preprocess):
	def __init__(self):
		super().__init__()
		self.name="one_hot_encode"

	def label_binarize(self,df, col_name):
		"""
		カテゴリ変数をone-hot化する関数です。
		データセットと列名を受け取り、その列のクラスラベルをone-hotに変換して
		データセットの最後の列に追加します。
		one-hot化された後のデータセットと変換規則を返します

		:param df: 学習に用いるデータセット
		:param col_name: one-hot化する列の列名
		"""
		le=LabelEncoder()
		le.fit(df[col_name])
		enc_col = pd.DataFrame(le.transform(df[col_name]),columns=[col_name])
		#enc_df = pd.concat([df, enc_col], axis=1)
		#enc_df = enc_df.drop(col_name, axis=1)

		lb = LabelBinarizer()
		lb.fit(enc_col)
		n_class=len(le.classes_)
		ohe_col = pd.DataFrame(lb.transform(enc_col),columns=[col_name+str(class_name) for class_name in le.inverse_transform(np.arange(n_class))])
		ohe_df = pd.concat([df, ohe_col], axis=1)
		ohe_df = ohe_df.drop(col_name, axis=1)

		#変換規則の登録
		self.bin_dict[col_name]=le

		return ohe_df

	def one_hot_encode(self,data):
		"""
		複数のカテゴリ変数をベクトル化して、それぞれ変換規則を保存する関数です。
		ベクトル化したデータセットを返します。
		変換規則はbin_dictに保存されています。

		:param data: 学習で用いるデータセット
		"""
		if self.columns!=None:
			self.bin_dict={}#one-hot用
			splited=self.columns.split(",")
			for spl in splited:
				data=self.label_binarize(data,spl)
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
		受けたcsv形式のデータフレームに対して、指定された列のone-hot encodeを行います
		出力はone-hot encode後のデータフレーム(csv形式)です
		また、変換規則に関するファイルonehot.jsonが生成されます
		上記ファイルをpredict.py実行時に指定してください
		"""

		parsed=self.parse_args(args)
		self.set_parsed_args_common(parsed)
		self.set_parsed_args_unique(parsed)

		#入力ファイル読み込み
		data=pd.read_csv(self.input)

		#one-hotエンコード
		encoded=self.one_hot_encode(data)

		#変換規則のファイル出力
		with open(self.temp_files_path.joinpath("onehot.pickle"),"wb") as f:
			pickle.dump(self.bin_dict,f)

		#前処理の順番を保存
		self.write_order()

		#エンコード後のデータセットの出力
		encoded.to_csv(self.output,index=False)
		# return encoded

if __name__=="__main__":
	onehot=One_hot_encode()
	onehot.main(sys.argv[1:])
