# coding: UTF-8

import argparse
import numpy as np
import pandas as pd
from sklearn import metrics
from sklearn.model_selection import cross_validate, cross_val_score
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.preprocessing import LabelBinarizer,LabelEncoder
import pickle
import sys

class Model():
	"""
	すべてのモデルの型である抽象クラスです。
	"""

	#def __init__(self):
	def make_parser(self):
		"""
        子クラスのmake_parser()によって内部的に呼ばれる関数です。
        共通オプションを追加したパーサーを返します。
        """
		parser = argparse.ArgumentParser()
		# 共通部分
		parser.add_argument("-i", "--input", dest="input",
							help="set input file", metavar="FILE", default=sys.stdin, type=open)
		parser.add_argument("-o", "--output", dest="output",
							help="set output file", metavar="FILE", default=None)

		return parser


	def set_parsed_args_common(self,parsed):
		"""
        共通のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """
		# 共通部分
		self.train_data=pd.read_csv(parsed.input)
		self.output=parsed.output



	def parse_args(self,args):
		"""
		コマンドライン引数をパースする関数です。
		すべてのオプションをパースしたものを返します。

		:param args: コマンドライン引数
		"""
		parser=self.make_parser()

		return parser.parse_args(args)


class Supervised(Model):
	def __init__(self):
		super().__init__()
		self.enc_dict = {}

	def make_parser(self):
		parser=super().make_parser()
		parser.add_argument("-s", "--scoring", dest="scoring", default="accuracy", type=str, help="set scoring type",
							choices=self.s_type
		)
		parser.add_argument("--kfold_type", dest="kfold_type", default="normal",
							help="set kfold type", choices=["normal", "stratified"])
		parser.add_argument("-n", "--n_splits", dest="n_splits",
							default=0, type=int, help="setting n_splits in cv", choices=range_check(low_limit=0))
		parser.add_argument("-t", "--target_colname", dest="target_colname",
							default="target", type=str, help="set target_colname")

		return parser

	def set_parsed_args_common(self,parsed):
		super().set_parsed_args_common(parsed)
		self.scoring = parsed.scoring
		self.kfold_type = parsed.kfold_type
		self.n_splits = parsed.n_splits
		self.target_colname = parsed.target_colname
		self.x_train = self.train_data.drop(self.target_colname, axis=1)
		self.y_train = self.train_data.loc[:, self.target_colname]

	def cross_validation(self,x_train,y_train,n_splits,scoring):
		"""
		クロスバリデーションを行う関数です。

		:param x_train: 説明変数が格納されたpandasのデータフレーム
		:param y_train: 目標変数が格納されたpandasのデータフレーム
		:param n_splits: クロスバリデーションを分割する個数を表す変数
		:param scoring: 評価方法を表す変数です。(s_typeを参照)
		"""
		# cv
		if n_splits > 1:
			scores = cross_validate(
				self.model, x_train, y_train, scoring=scoring, cv=n_splits, return_train_score=True)
			# scoreをcsvで出力
			pd.DataFrame(scores)[["train_score", "test_score"]
								 ].to_csv("scores.csv")


	def set_output(self):
		"""
		モデルの出力を設定する関数です。
		作成したモデルをファイルに書き出すか標準出力に書き込みます。
		出力先を返します。
		"""
		# ファイル書き込みかstdoutかで場合分け
		if type(self.output) == str:
			return open(self.output, 'wb')
		else:
			self.output="sys.stdout"
			return sys.stdout.buffer

	def write(self):
		"""
		作成したモデルを出力する関数です。
		set_outputで設定した出力先に出力します。
		"""
		#出力
		self.set_output().write(pickle.dumps(self))


class Regression(Supervised):
	"""
	回帰モデルの型となる抽象クラスです。
	"""
	def __init__(self):
		super().__init__()
		self.analysis_type="regression"
		# scoring_typeを定義
		self.s_type=[
			"mae",
			"mse",
			"msle"
			]

	def predict(self,x_test_original,x_test_preprocessed):
		"""
		テストデータに対する予測を出す関数です。
		予測結果とテストデータをマージしたものを返します。

		:param x_test_original: 前処理をしていない説明変数が格納されたpandasのデータフレーム
		:param x_test_preprocessed: 予測に用いる前処理済みの説明変数が格納されたpandasのデータフレーム
		"""
		pred=self.model.predict(x_test_preprocessed)
		pred_df=pd.DataFrame(pred,columns=["predict_"+self.target_colname])
		merged = pd.concat([pred_df, x_test_original], axis=1)
		return pred_df#merged


class Classification(Supervised):
	"""
	分類モデルの型となる抽象クラスです。
	"""
	def __init__(self):
		super().__init__()
		self.probability = False
		self.analysis_type="classification"
		# scoring_typeを定義
		self.s_type = [
			"accuracy",
			"f1",
			"f1_macro",
			"f1_micro",
			"f1_samples",
			"f1_weighted",
			"recall",
			"recall_macro",
			"recall_micro",
			"recall_samples",
			"recall_weighted",
			"neg_log_loss",
			"precision",
			"precision_macro",
			"precision_micro",
			"precision_samples",
			"precision_weighted"
		]


	def predict(self,x_test_original,x_test_preprocessed):
		"""
		テストデータに対する予測を出す関数です。
		self.probabilityにより、それぞれのクラスに属する確率を返すか、属する可能性が最も高いクラスのラベルを
		返すかを選択できます。
		予測結果とテストデータをマージしたものを返します。

		:param x_test_original: 前処理をしていない説明変数が格納されたpandasのデータフレーム
		:param x_test_preprocessed: 予測に用いる前処理済みの説明変数が格納されたpandasのデータフレーム
		"""
		if self.probability:
			 # テストデータに対する予測を出す
			pred = self.model.predict_proba(x_test_preprocessed)
			#もしターゲット列が文字列→連続値変換しているなら予測列名を要素名にする(例: prob_class:OK)
			if self.target_colname in self.enc_dict:
				n_class=len(self.enc_dict[self.target_colname].classes_)
				# predの列数に対応したカラム名をつける
				pred_df=pd.DataFrame(pred,columns=[
								"prob_class:"+str(class_name) for class_name in self.enc_dict[self.target_colname].inverse_transform(np.arange(n_class))])
			else:
				pred_df = pd.DataFrame(pred, columns=[
							   	"prob_class:" + str(i) for i in range(len(pred[0]))])
		else:
			pred=self.model.predict(x_test_preprocessed)
			pred_df=pd.DataFrame(pred,columns=["predict_"+self.target_colname])

		merged = pd.concat([pred_df, x_test_original], axis=1)  # 予測とテストデータセットを統合
		return pred_df#merged

class Clustering(Model):
	def __init__(self):
		super().__init__()
		self.analysis_type="clustering"

	def predict(self,x_test_original,x_test_preprocessed):
		pred=self.model.predict(x_test_preprocessed)
		pred_df=pd.DataFrame(pred,columns=["predict_class"])
		merged=pd.concat([pred_df,x_test_original],axis=1)
		return pred_df


class range_check(object):
	"""
	コマンドライン引数が適切かチェックするクラスです。
	make_parser()内のadd_argument()で使用します。
	"""

	def __init__(self, low_limit=None, high_limit=None, vtype="integer"):
		self.min = low_limit
		self.max = high_limit
		self.type = vtype

	def __contains__(self, val):
		ret = True
		if self.min is not None:
			ret = ret and (val >= self.min)
		if self.max is not None:
			ret = ret and (val <= self.max)
		return ret

	def __iter__(self):
		low = self.min
		if low is None:
			low = "-inf"
		high = self.max
		if high is None:
			high = "+inf"
		L1 = self.type
		L2 = " {} <= n <= {}".format(low, high)
		return iter((L1, L2))
