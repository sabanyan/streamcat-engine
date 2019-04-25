#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Regression
from sklearn.linear_model import ElasticNet
import pickle

class RKelastic(Regression):
    """
    elastic net回帰クラスです
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
        parser.add_argument("-a","--alpha",dest="alpha",help="weight of L1 term",type=float,default=1)
        parser.add_argument("--normalize",dest="normalize",help="whether use normalize",action='store_const',const=True,default=False)
        parser.add_argument("-b","--unuse_bias",dest="unuse_bias",help="whether use bias term",action='store_const',const=False)
        parser.add_argument("-r","--random_state",dest="random_state",help="set random_state(which is the seed used by the random number generator)",type=int,default=None)
        parser.add_argument("--tol",dest="tol",help="set tolerance for stopping criteria",type=float,default=1e-4)
        parser.add_argument("--l1_ratio",dest="l1_ratio",help="set l1 ratio against l2",default=0.5,type=float)
        return parser

    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """

        self.alpha=parsed.alpha
        self.normalize=parsed.normalize
        self.unuse_bias=parsed.unuse_bias
        self.random_state=parsed.random_state
        self.tol=parsed.tol
        self.l1_ratio=parsed.l1_ratio

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
        self.model=ElasticNet(
            alpha=self.alpha,
            random_state=self.random_state,
            fit_intercept=self.unuse_bias,
            tol=self.tol,
            l1_ratio=self.l1_ratio
            )
        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return

if __name__=="__main__":
    kelastic=RKelastic()
    kelastic.main(sys.argv[1:])
    kelastic.write()
