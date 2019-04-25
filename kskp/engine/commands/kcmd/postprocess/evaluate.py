#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd
import pickle
import sys
from sklearn import metrics
from sklearn.preprocessing import LabelBinarizer,LabelEncoder
import os
sys.path.append(os.getcwd()+"/modeling")
from classification import *
from regression import *
from predict import Predict
from pathlib import Path


class Evaluate():
    def __init__(self):
        self.classification_metrics={
            #分類用
            "accuracy":metrics.accuracy_score,
            "report":metrics.classification_report,#文字列
            "confusion_matrix":metrics.confusion_matrix,#行列
            "hamming":metrics.hamming_loss,
            "log":metrics.log_loss
            }
        self.regression_metrics={
            #回帰用
            "mae":metrics.mean_absolute_error,
            "mse":metrics.mean_squared_error,
            "log":metrics.mean_squared_log_error,
            "median":metrics.median_absolute_error
            }
        self.all_metrics={
            **self.classification_metrics,
            **self.regression_metrics
            }
        self.temp_files_path = Path(__file__).parent.parent.joinpath('preprocess/temp_files/')

    def parse_args(self, parser):
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--input", dest="input",
                            help="setting input file", metavar="FILE", default=sys.stdin)
        parser.add_argument("-o", "--output", dest="output",
                            help="setting output file", metavar="FILE", default=sys.stdout)
        parser.add_argument("-d", "--data", dest="test_data",
                            metavar="FILE", type=open, help="set test data")
        parser.add_argument("-p","--probability",dest="probability",help="set probability on",action="store_const",const=True,default=False)
        parser.add_argument("-m","--metrics",dest="metrics",help="select metrics appling model",choices=self.all_metrics.keys())
        parser.add_argument("--metrics_file_name",dest="metrics_file_name",default="metrics.csv",type=str)
        return parser#.parse_args(args)


    def main(self, args):
        pred=Predict()
        parser=self.parse_args(pred.make_parser())
        parsed = parser.parse_args(args)

        # testデータ読み込み
        test_data = pd.read_csv(parsed.test_data)
        #モデル読み込み
        pred.model=pred.read_model(parsed.input)
        #予測を確率で出すかどうかの設定(classificationクラスのみ有効)
        pred.model.probability=parsed.probability
        #クラスラベルの処理
        test_data_preprocessed=pred.preprocessing(test_data)
        #ターゲット列の分離
        with open(self.temp_files_path.joinpath("target_col_name.txt"),"r") as f:
            target_col_name=f.read()
        y_test=test_data_preprocessed[target_col_name]
        x_test=test_data_preprocessed.drop(columns = target_col_name)
        #予測
        pred_df=pred.model.predict(test_data,x_test)
        merged=pd.concat([pred_df,test_data],axis=1)

        #モデルの評価
        result=self.all_metrics[parsed.metrics](y_test,pred_df)

        #評価結果の出力(暫定)
        df = pd.DataFrame({result : parsed.metrics}, index=['1',])
        print(parsed.metrics)
        print(result)
        # result.to_csv(parsed.metrics_file_name,index=False)

        #出力
        pred.set_output(df,parsed.output)

        return

if __name__=="__main__":
    eval=Evaluate()
    eval.main(sys.argv[1:])
