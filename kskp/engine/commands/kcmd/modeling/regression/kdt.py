#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Regression
from sklearn.tree import DecisionTreeRegressor
import pickle


class RKdt(Regression):
    """
    決定木(回帰)クラスです。
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
        parser.add_argument("-l", "--min_samples_leaf", dest="min_samples_leaf",
                            help="setting min_samples_leaf", default=1,type=int)
        parser.add_argument("--min_samples_split", dest="min_samples_split",
                            help="setting min samples splits", default=2,type=int)
        parser.add_argument("-d", "--max_depth", dest="max_depth",
                            default=None, help="setting max_depth",type=int)
        parser.add_argument("-c","--criterion",dest="criterion",help="The function to measure the quality of a split",default="mse",type=str,choices=["mse","friendman_mse","mae"])
        parser.add_argument("-r","--random_state",dest="random_state",help="set random_state(which is the seed used by the random number generator)",default=None,type=int)
        return parser

    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """
        self.min_samples_leaf = parsed.min_samples_leaf
        self.max_depth = parsed.max_depth
        self.min_samples_split=parsed.min_samples_split
        self.criterion=parsed.criterion
        self.random_state=parsed.random_state

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
        self.model=DecisionTreeRegressor(
            min_samples_leaf=self.min_samples_leaf,
            max_depth=self.max_depth,
            min_samples_split=self.min_samples_split,
            random_state=self.random_state,
            criterion=self.criterion
            )
        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return

if __name__=="__main__":
    kdt=RKdt()
    kdt.main(sys.argv[1:])
    kdt.write()
