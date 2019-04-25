#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Classification
from sklearn.linear_model import LogisticRegression
import pickle

class CKlogreg(Classification):
    """
    ロジスティック回帰クラスです
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
        parser.add_argument("-C","--C",dest="C",help="Inverse of regularization strength",type=float,default=1)
        parser.add_argument("-p","--penalty",dest="penalty",help="select penalty term",choices=["l1","l2"],default="l2")
        parser.add_argument("-b","--unuse_bias",dest="unuse_bias",help="whether use bias term",action='store_const',const=False,default=True)
        parser.add_argument("-r","--random_state",dest="random_state",help="set random_state(which is the seed used by the random number generator)",type=int)
        parser.add_argument("--tol",dest="tol",help="set tolerance for stopping criteria",type=float,default=1e-4)
        parser.add_argument("-c","--class_weight",dest="class_weight",help="set class weight by dict",nargs="?",const="balanced",default=None,type=dict)

        return parser


    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """

        self.C=parsed.C
        self.penalty=parsed.penalty
        self.unuse_bias=parsed.unuse_bias
        self.random_state=parsed.random_state
        self.tol=parsed.tol
        self.class_weight=parsed.class_weight

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
        self.model=LogisticRegression(
            C=self.C,
            penalty=self.penalty,
            random_state=self.random_state,
            fit_intercept=self.unuse_bias,
            tol=self.tol,
            class_weight=self.class_weight
            )
        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return

if __name__=="__main__":
    klogreg=CKlogreg()
    klogreg.main(sys.argv[1:])
    klogreg.write()
