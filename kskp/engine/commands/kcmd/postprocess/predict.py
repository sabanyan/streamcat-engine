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
from pathlib import Path

class Predict():
    def __init__(self):
        self.preprocess_dict={
            "normalize":self.normalize,
            "standardize":self.standardize,
            "pca":self.pca,
            "one_hot_encode":self.one_hot_encode,
            "label_encode":self.label_encode
        }
        self.temp_files_path=Path(__file__).parent.parent.joinpath('preprocess/temp_files/')

    def make_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--input", dest="input",
                            help="setting input file", metavar="FILE", default=sys.stdin)
        parser.add_argument("-o", "--output", dest="output",
                            help="setting output file", metavar="FILE", default=sys.stdout)
        parser.add_argument("-d", "--data", dest="test_data",
                            metavar="FILE", type=open, help="set test data")
        parser.add_argument("-p","--probability",dest="probability",help="set probability on",action="store_const",const=True,default=False)

        return parser#.parse_args(args)

    def parse_args(self,args):
        parser=self.make_parser()

        return parser.parse_args(args)

    def read_model(self,parsed_input):
        """
        標準入力もしくはコマンドライン引数からモデルを読み込む
        """
        # inputがstdinかファイル指定かで場合分け
        if type(parsed_input) == str:
            with open(parsed_input, "rb") as f:
                return pickle.load(f)
        else:
            return pickle.loads(
                parsed_input.buffer.read())  # 今のところこの仕様とする

    def set_output(self,merged,parsed_output):
        """
        マージしたデータセットを.csvまたは標準出力に出力する
        """
        # outputがstdoutかファイル出力かで場合分け
        # if type(parsed_output) == str:
        #     #output = open(parsered.output, 'wb')
        #     merged.to_csv(parsed_output,index=False)  # 出力先が指定されている場合、csv形式で出力する
        # else:
        #     output = parsed_output.buffer  # されていない場合は標準出力
        #     output.write(pickle.dumps(merged))
        # return

        # 元々は上記の記述だっが、csvとして標準入力に流したかったので、下記の出力記述方法にした
        # とりあえず何かあったときのために上記の出力方法もコメントアウトで残しておく
        merged.to_csv(parsed_output,index=False)

    def normalize(self,x_test):
        if os.path.isfile(self.temp_files_path.joinpath("normalize.pickle")):
            #変換規則のファイル読み取り
            with open(self.temp_files_path.joinpath("normalize.pickle","rb")) as f:
                self.model.norm_dict=pickle.load(f)
            #正規化
            for col_name in self.model.norm_dict:
                col=x_test[col_name].values.reshape((-1,1))
                mms=self.model.norm_dict[col_name]
                x_test[col_name]=pd.DataFrame(np.array(mms.transform(col)).reshape((-1,1)),columns=self.model.norm_dict)
            os.remove(self.temp_files_path.joinpath("normalize.pickle"))
        return x_test

    def standardize(self,x_test):
        if os.path.isfile(self.temp_files_path.joinpath("standardize.pickle")):
            #変換規則のファイル読み取り
            with open(self.temp_files_path.joinpath("standardize.pickle"),"rb") as f:
                self.model.std_dict=pickle.load(f)
            #標準化
            for col_name in self.model.std_dict:
                col=x_test[col_name].values.reshape((-1,1))
                sc=self.model.std_dict[col_name]
                x_test[col_name]=pd.DataFrame(np.array(sc.transform(col)).reshape((-1,1)),columns=self.model.std_dict)
            os.remove(self.temp_files_path.joinpath("standardize.pickle"))
        return x_test

    def label_encode(self,x_test):
        if os.path.isfile(self.temp_files_path.joinpath("label.pickle")):
            #変換規則のファイル読み取り
            with open(self.temp_files_path.joinpath("label.pickle"),"rb") as f:
                self.model.enc_dict=pickle.load(f)
            #ノーマルエンコード
            for col_name in self.model.enc_dict:
                if col_name==self.model.target_colname:
                    continue
                le=self.model.enc_dict[col_name]
                encoded=self.model.enc_dict[col_name].transform(x_test[col_name])
                x_test[col_name]=pd.DataFrame(encoded,columns=[col_name])
            os.remove(self.temp_files_path.joinpath("label.pickle"))
        return x_test

    def one_hot_encode(self,x_test):
        if os.path.isfile(self.temp_files_path.joinpath("onehot.pickle")):
            #変換規則のファイル読み取り
            with open(self.temp_files_path.joinpath("onehot.pickle"),"rb") as f:
                self.model.bin_dict=pickle.load(f)
            #one-hotエンコード
            for col_name in self.model.bin_dict:
                le=self.model.bin_dict[col_name]
                enc_col=pd.DataFrame(le.transform(x_test[col_name]),columns=[col_name])
                lb=LabelBinarizer()
                lb.fit(enc_col)
                n_class=len(le.classes_)
                encoded=pd.DataFrame(lb.transform(enc_col),columns=[col_name+str(class_name) for class_name in le.inverse_transform(np.arange(n_class))])
                x_test=pd.concat([x_test,encoded],axis=1)
                x_test=x_test.drop(col_name,axis=1)
            os.remove(self.temp_files_path.join("onehot.pickle"))
        return x_test

    def pca(self,x_test):
        if os.path.isfile(self.temp_files_path.joinpath("pca.pickle")):
            with open(self.temp_files_path.joinpath("pca.pickle"),"rb") as f:
                self.model.pca=pickle.load(f)
            x_test=self.model.pca.transform(x_test)
            os.remove(self.temp_files_path.joinpath("pca.pickle"))
        return x_test

    def preprocessing(self,x_test):
        """
        前処理で作成した変換規則から、テストデータのクラスラベルをベクトルに変換する
        preprocessingをここに並べていく(要検討)

        """
        #前処理の順番が記述されているpreprocess_order.txtがあればテストデータに対しても前処理を行う
        if os.path.isfile(self.temp_files_path.joinpath("preprocess_order.txt")):
            with open(self.temp_files_path.joinpath("preprocess_order.txt"),"r") as f:
                preprocess_order=f.read()
            preprocess_order=preprocess_order.split(",")

            for preprocess in preprocess_order:
                x_test=self.preprocess_dict[preprocess](x_test)

            os.remove(self.temp_files_path.joinpath("preprocess_order.txt"))


        return x_test


    def main(self,args):
        parsed = self.parse_args(args)

        # testデータ読み込み
        x_test_original = pd.read_csv(parsed.test_data)
        #モデル読み込み
        self.model=self.read_model(parsed.input)
        #予測を確率で出すかどうかの設定(classificationクラスのみ有効)
        self.model.probability=parsed.probability
        #クラスラベルの処理
        x_test_preprocessed=self.preprocessing(x_test_original)
        #予測
        pred_df=self.model.predict(x_test_original,x_test_preprocessed)
        merged=pd.concat([pred_df,x_test_original],axis=1)
        #出力
        self.set_output(merged,parsed.output)

        return

if __name__=="__main__":
    pred=Predict()
    pred.main(sys.argv[1:])
    #main(sys.argv[1:])
