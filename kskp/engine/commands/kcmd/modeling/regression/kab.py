#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Regression
from sklearn.ensemble import AdaBoostRegressor
import pickle


class RKab(Regression):
    """
    アダブースト(回帰)クラスです。
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
        parser.add_argument("-l", "--learning_rate", dest="learning_rate",
                            help="set learning_rate", default=1,type=int)
        parser.add_argument("--loss",dest="loss",help="set loss function",default="linear",choices=["linear","square","exponential"],type=str)
        parser.add_argument("-r","--random_state",dest="random_state",help="set random_state(which is the seed used by the random number generator)",default=None,type=int)
        parser.add_argument("-a","--algorithm",dest="algorithm",help="set algorithm",default="SAMME.R",type=str,choices=["SAMME.R","SAMME"])
        parser.add_argument("--n_estimators",dest="n_estimators",help="set the number of estimators",default=50,type=int)
        return parser

    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """
        self.learning_rate = parsed.learning_rate
        self.random_state=parsed.random_state
        self.n_estimators=parsed.n_estimators
        self.loss=parsed.loss

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
        self.model=AdaBoostRegressor(
                learning_rate=self.learning_rate,
                random_state=self.random_state,
                n_estimators=self.n_estimators,
                loss=self.loss)

        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return

if __name__=="__main__":
    kab=RKab()
    kab.main(sys.argv[1:])
    kab.write()
