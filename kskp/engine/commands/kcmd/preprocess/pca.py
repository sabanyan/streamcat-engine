#!/usr/bin/env python3
from kskp.engine.commands.kcmd.preprocess.common.preprocess import Preprocess
# from common.preprocess import Preprocess
from sklearn.decomposition import PCA
import numpy as np
import pandas as pd
import sys
import pickle

class Pca(Preprocess):
    """
    主成分分析クラスです

    """
    def __init__(self):
        super().__init__()
        self.name="pca"

    def make_parser(self):
        parser=super().make_parser()
        parser.add_argument("--n_components",dest="n_components",default=2,type=int)
        return parser

    def set_parsed_args_unique(self,parsed):
        self.n_components=parsed.n_components

    def parse_args(self,args):
        parser=self.make_parser()
        return parser.parse_args(args)

    def pca(self,data):
        self.model=PCA(n_components=self.n_components)
        self.model.fit(data)
        transformed=self.model.transform(data)
        transformed=pd.DataFrame(transformed,columns=["pca_"+str(i+1) for i in range(self.n_components)])
        return transformed


    def main(self,args):
        parsed=self.parse_args(args)
        self.set_parsed_args_common(parsed)
        self.set_parsed_args_unique(parsed)

        data=pd.read_csv(self.input)

        #教師あり学習ならtarget列を分離しておく
        if "target" in data.columns:
            isSupervised=True
        else:
            isSupervised=False
        if isSupervised:
            target=data["target"]
            data=data.drop("target",axis=1)
        #主成分分析
        output_df=self.pca(data)

        #変換規則のファイル出力
        with open(self.temp_files_path.joinpath("pca.pickle"), "wb") as f:
            pickle.dump(self.model,f)

        #教師あり学習ならtarget列を結合
        if isSupervised:
            output_df=pd.concat([target,output_df],axis=1)

        #前処理の順番を保存
        self.write_order()

        #主成分データセット出力
        output_df.to_csv(self.output,index=False)
        # return output_df

if __name__=="__main__":
    pca=Pca()
    pca.main(sys.argv[1:])
