#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd()+"/modeling/common")
from Model import Classification
from sklearn.neural_network import MLPClassifier
import pickle

class CKneural_network(Classification):
    """
    ニューラルネットワーク(分類)クラスです
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
        parser.add_argument("--hidden_layer_sizes",dest="hidden_layer_sizes",help="set the number of neurons in its hidden layer sizes",type=tuple,default=(100,))
        parser.add_argument("-a","--activation",dest="activation",help="select activation",choices=["identity","logistic","tanh","relu"],default="relu")
        parser.add_argument("--solver",dest="solver",help="select optimizer",choices=["lbfgs","sgd","adam"],default="adam")
        parser.add_argument("--alpha",dest="alpha",help="set weight of L2 penalty term",type=float,default=1e-4)
        parser.add_argument("--tol",dest="tol",help="set tolerance for the optimization",type=float,default=1e-4)
        parser.add_argument("--learning_rate_init",dest="learning_rate_init",help="set initial learning rate",default=1e-3,type=float)
        parser.add_argument("--early_stopping",dest="early_stopping",help="whether to use early_stopping",default=False,action="store_const",const=True)
        parser.add_argument("--momentum",dest="momentum",help="set momentum for gradient descent update.Only used when optimizer=sgd",default=0.9,type=float)
        parser.add_argument("--epsilon",dest="epsilon",help="set value for numerical stability in adam.Only used when optimizer=adam",default=1e-8,type=float)
        return parser


    def set_parsed_args_unique(self,parsed):
        """
        固有のオプションを属性に追加する関数です。

        :param parsed:　コマンドライン引数をパースしたもの
        """

        self.hidden_layer_sizes=parsed.hidden_layer_sizes
        self.activation=parsed.activation
        self.solver=parsed.solver
        self.alpha=parsed.alpha
        self.tol=parsed.tol
        self.learning_rate_init=parsed.learning_rate_init
        self.early_stopping=parsed.early_stopping
        self.momentum=parsed.momentum
        self.epsilon=parsed.epsilon

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
        self.model=MLPClassifier(
            hidden_layer_sizes=self.hidden_layer_sizes,
            activation=self.activation,
            alpha=self.alpha,
            solver=self.solver,
            tol=self.tol,
            learning_rate_init=self.learning_rate_init,
            early_stopping=self.early_stopping,
            momentum=self.momentum,
            epsilon=self.epsilon
            )
        # cv
        self.cross_validation(self.x_train,self.y_train,self.n_splits,self.scoring)

        # モデルの学習
        self.model=self.model.fit(self.x_train,self.y_train)
        #出力
        #self.set_output().write(pickle.dumps(self))

        return

if __name__=="__main__":
    knn=CKneural_network()
    knn.main(sys.argv[1:])
    knn.write()
