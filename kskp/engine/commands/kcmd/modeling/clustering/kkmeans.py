#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from kskp.engine.commands.kcmd.modeling.common.Model import Clustering
from sklearn.cluster import KMeans
import pickle
import pandas as pd
import numpy as np


class Kkmeans(Clustering):
    def __init__(self):
        super().__init__()


    def make_parser(self):
        """
        parse_argsによって内部的に呼ばれる関数です。
        共通オプションを追加するsuper().make_parser()を実行した後、固有オプションを追加したパーサーを返します。
        """
        # 固有部分
        parser=super().make_parser()
        parser.add_argument("--n_clusters",dest="n_clusters",help="set the number of clusters",type=int,default=8)
        parser.add_argument("--n_init",dest="n_init",help="select penalty term",type=int,default=10)
        parser.add_argument("--max_iter",dest="max_iter",help="set the maximum number of iteration",type=int,default=300)
        parser.add_argument("--precompute_distances",dest="precompute_distances",help="whether precompute distances",choices=["auto",True,False],default="auto")
        parser.add_argument("--tol",dest="tol",help="set tolerance for stopping criteria",type=float,default=1e-4)

        return parser


    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """

        self.n_clusters=parsed.n_clusters
        self.n_init=parsed.n_init
        self.max_iter=parsed.max_iter
        self.precompute_distances=parsed.precompute_distances
        self.tol=parsed.tol

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
        self.model=KMeans(
            n_clusters=self.n_clusters,
            n_init=self.n_init,
            max_iter=self.max_iter,
            precompute_distances=self.precompute_distances,
            tol=self.tol
            )
        # cv
        #self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.train_data)
        pred=self.model.predict(self.train_data)
        pred_df=pd.DataFrame(pred,columns=["predict_class"])
        merged=pd.concat([pred_df,self.train_data],axis=1)
        # merged.to_csv(self.output)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return merged
if __name__ == '__main__':
    kkmeans=Kkmeans()
    kkmeans.main(sys.argv[1:])
