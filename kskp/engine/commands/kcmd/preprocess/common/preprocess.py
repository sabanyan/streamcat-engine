import os
import sys
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


class Preprocess():
	def __init__(self):
		self.temp_files_path = Path(__file__).parent.parent.joinpath('temp_files/')
		self.preprocess_list = [
						'normalize.pickle',
						'standardize.pickle',
						'label.pickle',
						'onehot.pickle',
						'pca.pickle',
						'preprocess_order.txt',
						'target_col_name.txt'
						]

	def make_parser(self):
		"""
		子クラスのmake_parser()によって内部的に呼ばれる関数です。
		共通オプションを追加したパーサーを返します。
		"""
		parser = argparse.ArgumentParser()

		parser.add_argument('-i', '--input', dest='input',
			help='set input file name on first preprocess', default=sys.stdin, type=str)
		parser.add_argument('-o', '--output', dest='output',
			help='set output file name if you want', default=sys.stdout, type=str)

		return parser

	def set_parsed_args_common(self, parsed):
		"""
		共通のオプションを属性に追加する関数です。

		:param parsed:　コマンドライン引数をパースしたもの
		"""

		self.input = parsed.input
		self.output = parsed.output

	def parse_args(self, args):
		"""
		コマンドライン引数をパースする関数です。
		すべてのオプションをパースしたものを返します。

		:param args: コマンドライン引数
		"""
		parser = self.make_parser()

		return parser.parse_args(args)

	def write_order(self):
		"""
		前処理の順番をpreprocess_order.txtに書き込みます
		"""

		# 二番目以降の処理なら追加書き込み
		path = self.temp_files_path.joinpath('preprocess_order.txt')
		if os.path.isfile(path):
			with open(path, 'a') as f:
				f.write(',' + self.name)
		# 最初の処理なら.txtを作成して書き込み
		else:
			with open(path, 'w') as f:
				f.write(self.name)

	def remove_temp_files(self):
		# 中間ファイルのフォルダがなければ作成
		if not os.path.isdir(self.temp_files_path):
			os.mkdir(self.temp_files_path)

		# 中間ファイルの削除
		for filename in self.preprocess_list:
			if os.path.isfile(self.temp_files_path.joinpath(filename)):
				os.remove(self.temp_files_path.joinpath(filename))
