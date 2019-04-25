#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Classification
from sklearn.ensemble import BaggingClassifier
import pickle


class CKbag(Classification):
    """
    バギング(分類)クラスです。
    """
    def __init__(self):
        super().__init__()


    def make_parser(self):
        """
        parse_argsによって内部的に呼ばれる関数です。
        共通オプションを追加するsuper().make_parser()を実行した後、固有オプションを追加したパーサーを返します。
        """
        #固有部分
        parser=super().make_parser()
        parser.add_argument("-r","--random_state",dest="random_state",help="set random_state(which is the seed used by the random number generator)",default=None,type=int)
        parser.add_argument("--n_estimators",dest="n_estimators",help="set the number of estimators",default=50,type=int)
        parser.add_argument("--max_samples",dest="max_samples",help="The number of samples to draw from X to train each base estimator",default=1.0,type=float)
        parser.add_argument("--unuse_bootstrap",dest="unuse_bootstrap",help="whether use bootstrap sampling",default=True,const=False,action="store_const")
        parser.add_argument("--max_features",dest="max_features",help="The number of features to draw from X to train each base estimator",default=1.0,type=float)
        parser.add_argument("--unuse_bootstrap_features",dest="unuse_bootstrap_features",help="whether features are drawn with replacement",default=True,const=False,action="store_const")
        return parser

    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """
        self.random_state=parsed.random_state
        self.n_estimators=parsed.n_estimators
        self.max_samples=parsed.max_samples
        self.unuse_bootstrap=parsed.unuse_bootstrap
        self.unuse_bootstrap_features=parsed.unuse_bootstrap_features
        self.max_features=parsed.max_features


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
        self.model=BaggingClassifier(
                max_samples=self.max_samples,
                max_features=self.max_features,
                bootstrap=self.unuse_bootstrap,
                bootstrap_features=self.unuse_bootstrap_features,
                random_state=self.random_state,
                n_estimators=self.n_estimators)

        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return

if __name__=="__main__":
    kbag=CKbag()
    kbag.main(sys.argv[1:])
    kbag.write()
