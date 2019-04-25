#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Classification
from sklearn.neighbors import KNeighborsClassifier
import pickle

class CKnearest_neighbors(Classification):
    """
    最近傍法(分類)クラスです
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
        parser.add_argument("--n_neighbors",dest="n_neighbors",help="set the number of neighbors",type=int,default=5)
        parser.add_argument("--weights",dest="weights",help="weight function used on prediction",choices=["uniform","distance"],default="uniform")
        parser.add_argument("-a","--algorithm",dest="algorithm",help="select algorithm",choices=["auto","ball_tree","kd_tree","brute"],default="auto")
        parser.add_argument("--leaf_size",dest="leaf_size",help="set leaf size passed to BallTree or KDTree",type=int,default=30)
        parser.add_argument("-p","--p",dest="p",help="set power param for the Minkowski loss",type=int,default=2)
        return parser


    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """

        self.n_neighbors=parsed.n_neighbors
        self.weights=parsed.weights
        self.algorithm=parsed.algorithm
        self.leaf_size=parsed.leaf_size
        self.p=parsed.p


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
        self.model=KNeighborsClassifier(
            n_neighbors=self.n_neighbors,
            weights=self.weights,
            algorithm=self.algorithm,
            leaf_size=self.leaf_size,
            p=self.p
            )
        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return

if __name__=="__main__":
    knn=CKnearest_neighbors()
    knn.main(sys.argv[1:])
    knn.write()
