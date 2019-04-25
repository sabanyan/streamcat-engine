#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Regression
from sklearn import svm
import pickle

class RKsvm(Regression):
    """
    サポートベクターマシン(回帰)クラスです。
    """
    def __init__(self):
        super().__init__()

    def make_parser(self):
        """
        parse_argsによって内部的に呼ばれる関数です。
        共通オプションを追加するsuper().make_parser()を実行した後、固有オプションを追加したパーサーを返します。
        """
        # 固有部分
        parser=super().make_parser()
        parser.add_argument("-c", "--C", dest="C",help="setting penalty parameter C of the error term", default=1.0, type=float)
        parser.add_argument(
            "-k", "--kernel", dest="kernel", default="rbf", type=str,
            help="setting kernel function", choices=['linear', 'poly', 'rbf', 'sigmoid', 'precomputed']
        )
        parser.add_argument("-g", "--gamma", dest="gamma", default=0.1, type=float,  # choiceを明確にする！
                            help="setting kernel coefficient for ‘rbf’, ‘poly’ and ‘sigmoid’. If gamma is ‘auto’ then 1/n_features will be used instead.")

        return parser

    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """
        self.kernel = parsed.kernel
        self.C = parsed.C
        self.gamma =parsed.gamma

    def main(self,args):
        """
        メイン関数です。
        ・コマンドライン引数の処理
        ・モデルの初期化
        ・クロスバリデーション
        ・モデルの学習
        を行います。
        """

        #コマンドライン引数をパース
        parsed=self.parse_args(args)
        #共通オプション
        self.set_parsed_args_common(parsed)
        # 固有オプション
        self.set_parsed_args_unique(parsed)
        # モデル生成
        self.model=svm.SVR(C=self.C, kernel=self.kernel, gamma=self.gamma)
        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)
        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)

        return

if __name__=="__main__":
    ksvm=RKsvm()
    ksvm.main(sys.argv[1:])
    ksvm.write()
