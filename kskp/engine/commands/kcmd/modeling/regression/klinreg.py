#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Regression
from sklearn.linear_model import LinearRegression
import pickle

class RKlinreg(Regression):
    """
    線形回帰クラスです。
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
        parser.add_argument("--normalize",dest="normalize",help="whether use normalize",action='store_const',const=True,default=False)

        return parser

    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """
        self.normalize=parsed.normalize

    def main(self,args):
        """
        メイン関数です。
        ・コマンドライン引数の処理
        ・モデルの初期化
        ・クロスバリデーション
        ・モデルの学習
        を行います。

        :param args: コマンドライン引数
        """

        #コマンドライン引数をパース
        parsed=self.parse_args(args)
        #共通オプション
        self.set_parsed_args_common(parsed)
        # 固有オプション
        self.set_parsed_args_unique(parsed)
        # モデル生成
        self.model=LinearRegression(normalize=self.normalize)
        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)
        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)

        return

if __name__=="__main__":
    klinreg=RKlinreg()
    klinreg.main(sys.argv[1:])
    klinreg.write()
