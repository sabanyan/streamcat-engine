#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Classification
from sklearn.naive_bayes import GaussianNB
import pickle

class CKgaussian_nb(Classification):
    """
    ナイーブベイズ(分類)クラスです
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
        parser.add_argument("--priors",dest="priors",help="set prior probabilities of the classes")
        return parser


    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """

        self.priors=parsed.priors


    def main(self,args):
        """
        メイン関数です。
        ・コマンドライン引数の処理
        ・モデルの初期化
        ・クロスバリデーション
        ・モデルの学習
        を行います。
        """

        parsed=self.parse_args(args)#引数の処理

        # 引数から変数に
        #共通部分
        self.set_parsed_args_common(parsed)
        # 固有部分
        self.set_parsed_args_unique(parsed)
        # モデル生成
        self.model=GaussianNB(
            priors=self.priors
            )
        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return

if __name__=="__main__":
    kgnb=CKgaussian_nb()
    kgnb.main(sys.argv[1:])
    kgnb.write()
