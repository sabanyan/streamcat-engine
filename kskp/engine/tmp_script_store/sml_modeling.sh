#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.1"

#外部モジュール参照
readonly  SCRIPT_PATH=$(cd $(dirname $0); pwd) #このスクリプトの絶対パス
# MCMD使用
# KCMD使用

#注意 mbest は、evaluate.py 出力行数が開発時から増加したためと思われる重複行が出現するため追加

# 注意事項
# ・デモ用に暫定的に作成したもののため、後日 仕様変更、差し替えが前提
# ・原稿の引数で、未実装の機能
#    - k 集計キー指定         ※キー指定が無い場合、処理をしない
#    - 予測値の出力           ※分類の場合、predict.py でエラー発生のため
#      output_predict_data=   症状：マルチバイト文字列を分類したい場合、失敗する可能性あり
#    - 学習済モデル保存        ※ファイル名決めなど 仕様 不確定
#      model_data_path=       全てのモデルの保存がされないが、精度評価のためテンポラリへの出力が必要
#    - パス設定関連           ※KCOMDの扱いが難しいため、フルパス指定＆作業パス移動実施
#    - 精度評価指標           ※現状 1列 2行 （指標名、値）のみ 意図通り動作する
#      metrics_list=              2行以上、2列以上 出力される指標には、未対応  動作も未検証
#                             ｋコマンド側も出力仕様の見直しが必要と考えられる
#                             使用可：分類   accuracy
#                                    回帰   mae, mse, median
#    - 学習データの件数出力
#    - ロジックへのパラメータの出力
#--------------------------------------------------------------
# sml_modeling  教師あり学習モデリング
#--------------------------------------------------------------
#
# 引数として与えらた変数
#    [-classification]  分類を行う。 省略時は回帰
#    target_list=       目的変数の項目名リスト
#    [feature_list=]    説明変数の項目名リスト。 省略時はデータ項目から設定する
#    [exclude_list=]    説明変数から除外する項目名リスト
#    [k=]               集計キー項目をカンマ区切りで与える
#                       変数：group_key_list
#    command_list=      ロジックとパラメータを実行するコマンド文のリスト
#                       形式 コマンドへの引数記述を含めた文字列を、カンマ区切りで連結し、"全文" として与える
#                           "コマンド パラメータ... , コマンド パラメータ..."
#    [metrics_list=]    評価指標名のリスト。 省略時はデフォルトを設定
#
#    [i=]               入力ファイル名を指定する。省略時は、標準入力を処理する
#                       変数：input_file      入力ファイル名
#    [output_predict_data=] 予測値データ出力ファイル名
#    [output_metrics_data=] 学習精度評価データ出力ファイル名
#    model_data_path    モデルファイルの出力先フォルダのパス
#    temp_path          テンポラリファイル出力先
#    kcmd_path          KCMDのホームディレクトリ
#--------------------------------------------------------------
function usage() {
    echo "${PROGNAME} ： グループ別処理"
    echo "==========="
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} "
    echo
    echo "例"
    echo "${PROGNAME} "

    exit 1
}

# エラー処理
set -e -u -o pipefail   # パイプ処理中にエラー発生で処理を終了する設定
error(){
  echo "#ERROR# Stoped ${PROGNAME}"
  echo "[ ${BASH_SOURCE} : ${LINENO} ] returns not zero status"
  #後処理
  IFS=${OLDIFS}   # bash環境変数を元に戻す
  exit 1
}
trap error ERR

# 引数の格納用変数、デフォルト値のセット
classification=""           #分類 or 回帰の判断用
target_list=""
feature_list=""
exclude_list=""
command_list=""
metrics_list=""
group_key_list=""
input_file=""               #分析対象とするデータファイル名
output_predict_data=""
output_metrics_data=""
model_data_path=""
temp_path=""
kcmd_path=""

param=""
for OPT in "$@"
do
#  echo $OPT
    case "$OPT" in
        '-h'|'--help' )
            usage
            exit 1
            ;;
        '--version' )
            echo ${VERSION}
            exit 1
            ;;
        '-classification' )
            classification="-classification"
            shift 1
            ;;
        'target_list='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            target_list=${p_value}
            shift 1
            ;;
        'feature_list='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            feature_list=${p_value}
            shift 1
            ;;
        'exclude_list='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            exclude_list=${p_value}
            shift 1
            ;;
        'command_list='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            command_list=${p_value//"'"/""}
            shift 1
            ;;
        'metrics_list='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            metrics_list=${p_value}
            shift 1
            ;;
        'k='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            group_key_list=${p_value}
            shift 1
            ;;
        'i='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            input_file=${p_value}
            shift 1
            ;;
        'output_predict_data='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            output_predict_data=${p_value}
            shift 1
            ;;
        'output_metrics_data='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            output_metrics_data=${p_value}
            shift 1
            ;;
        'model_data_path='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            model_data_path=${p_value}
            shift 1
            ;;
        'temp_path='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            temp_path=${p_value}
            shift 1
            ;;
        'kcmd_path='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            kcmd_path=${p_value}
            shift 1
            ;;
        '--'|'-' )
            shift 1
            break
            ;;
        *)
            echo "$PROGNAME: illegal option -- '$(echo $1 | sed 's/^-*//')'" 1>&2
            exit 1
            ;;
    esac
done


#if [[ -z $param ]]; then
#    echo "$PROGNAME: too few arguments" 1>&2
#    echo "Try '$PROGNAME --help' for more information." 1>&2
#    exit 1
#fi


#==========================================================
# 分析コマンド処理
#==========================================================
readonly default_metrics_regresion="mae,mse"           # 回帰のデフォルト精度評価指標
readonly default_metrics_classification="accuracy"     # 分類の 〃
tmp_input_file="/Users/ygt1qa/dev/KSKP/kskp-flow-engine/_tmp_stdin_"   # 標準入力のファイル出力名
input_file_header=""

# 標準入力のファイル化
if [[ -z ${input_file} ]]; then
  cat /dev/stdin > ${tmp_input_file}
else
  tmp_input_file=${input_file}
fi

# 出力ファイルの初期化
tmp_output_metrics_data=""
if [[ -n ${output_metrics_data} ]]; then
  rm -f ${output_metrics_data}
  tmp_output_metrics_data=${output_metrics_data}
else
  tmp_output_metrics_data="/dev/stdout"
fi


#-------
readonly OLDIFS=${IFS}   # bash 環境変数の記録
#-------
# ヘッダーの取得
input_file_header=`head -1 ${tmp_input_file}`
input_file_header=${input_file_header}

IFS=','               # 以降 カンマ区切りに変更  空白文字含む項目名、コマンド文 対応
  declare -a array_input_file_header=(${input_file_header})
  declare -a array_target_list=(${target_list})
  declare -a array_feature_list=(${feature_list})
  declare -a array_exclude_list=(${exclude_list})
  declare -a array_command_list=(${command_list})
  declare -a array_metrics_list=(${metrics_list})
  declare -a array_group_key_list=(${group_key_list})
IFS=${OLDIFS}         # 区切りを元に戻す


# 評価指標リストが指定されなかった場合のセット
if [[ -z ${metrics_list} ]]; then
  :
  if [[ -z ${classification} ]]; then
    metrics_list=${default_metrics_regresion}
  else
    metrics_list=${default_metrics_classification}
  fi
  IFS=','               # 以降 カンマ区切りに変更  空白文字含む項目名、コマンド文 対応
  array_metrics_list=${metrics_list}
  IFS=${OLDIFS}         # 区切りを元に戻す
fi

# 特徴量リストが引数指定されなかった場合の項目名リストのセット
# for文は、配列の添字でループする  ※理由：空白含む文字列対策のため
# 引数指定とデータ項目名の比較時、NYSOLが出力する %数字 を除去する
if [[ -z ${feature_list} ]]; then
    for i in "${!array_input_file_header[@]}"; do
      org_i=$i
      i=${array_input_file_header[$i]}
#      i=`echo $i | tr '[:lower:]' '[:upper:]'`
      addflg=1
      for j in "${!array_target_list[@]}"; do
        j=${array_target_list[$j]}
#        j=`echo $j | tr '[:lower:]' '[:upper:]'`
        if [ ${i%\%*} = ${j%\%*} ]; then
          addflg=0
          break
        fi
      done

      if [ ${addflg} = 1 ]; then
        for j in "${!array_exclude_list[@]}"; do
          j=${array_exclude_list[$j]}
#          j=`echo $j | tr '[:lower:]' '[:upper:]'`
          if [ ${i%\%*} = ${j%\%*} ]; then
            addflg=0
            break
          fi
        done
      fi

      if [ ${addflg} = 1 ]; then
        for j in "${!array_group_key_list[@]}"; do
          j=${array_group_key_list[$j]}
#          j=`echo $j | tr '[:lower:]' '[:upper:]'`
          if [ ${i%\%*} = ${j%\%*} ]; then
            addflg=0
            break
          fi
        done
      fi

      if [ ${addflg} = 1 ]; then
        array_feature_list+=(${array_input_file_header[org_i]})
      fi
    done
fi

#---------------------------------------
# 処理の概要
#   入力データより、グループキー項目で一意にしたデータを作成し、
#   グループキー項目で、入力データを行選択したデータか、
#   グループ別処理しない場合は全てのデータに対して、
#   コマンドリストで指定された数だけ、以下を行う。
#     機械学習を実行・モデルデータ保存
#     学習精度評価
#     予測値データ作成
#---------------------------------------
readonly tmp_group_key_data="${temp_path}/group_key"
readonly tmp_training_data="${temp_path}/training_data"

# echo 引数設定値
# echo 目的変数： ${target_list}
# echo 説明変数： ${feature_list}
# echo 評価指標： ${metrics_list}
# echo コマンド： ${command_list}
# echo グループ： ${group_key_list}
# echo
# echo 内部 目的変数：${array_target_list[@]}
# echo 内部 説明変数：${array_feature_list[@]}
# echo 内部 評価指標：${array_metrics_list[@]}
# echo 内部 コマンド：${array_command_list[@]}
# echo 内部 グループ：${array_group_key_list[@]}

declare -a array_group_key_data_header
declare -a array_group_key_data
readonly DATA_NUM="NUM"                       #データ数の列名
readonly MODEL_TYPE_FLD_NAME="MODEL_TYPE"
readonly MODEL_TYPE_FLD_VAL_CLSSIFICATION="C" #分類
readonly MODEL_TYPE_FLD_VAL_REGRESSION="R"    #回帰
readonly TARGET_FLD_BASE_NAME="TARGET"        #目標変数列名のベース
readonly FEATURE_NAME="FEATURE"               #特徴量リストの名前
readonly FEATURE_NUM="FEATURE_NUM"            #特徴量の数
readonly LOGIC_NAME="LOGIC"                   #分析ロジック名の列名
readonly LOGIC_PARM_NAME="PARM"               #分析ロジックのパラメータの列名
readonly METRICS_NAME="METRICS"               #評価指標名の列名
readonly METRICS_VALUE="METRICS_VALUE"

#-----------------------
# mcutで使用する学習用データの列選択条件
#-----------------------
col_expression=""
top=1
for j in ${array_target_list[@]}; do
  if [ ${top} = 1 ]; then
    col_expression=${j%\%*}
    top=0
  else
    col_expression=${col_expression},$j
  fi
done
for j in ${array_feature_list[@]}; do
  col_expression=${col_expression},${j%\%*}
done


#-----------------------
# グループ別処理
#-----------------------
cd ${kcmd_path}

top_output_head=1
if [[ -n ${group_key_list} ]]; then
  top_flg=1
  key_num=0   # グループ別処理時のキー項目数のカウント

  muniq k=${group_key_list} i=${tmp_input_file} |
  mcut  f=${group_key_list} > ${tmp_group_key_data}

  while read line
  do
    IFS=','               # 以降 カンマ区切りに変更  空白文字含む項目名、コマンド文 対応
      unset array_group_key_data
      array_group_key_data=(${line})
    IFS=${OLDIFS}         # 区切りを元に戻す
    # 先頭行の処理
    if [ ${top_flg} = 1 ]; then
      array_group_key_data_header=("${array_group_key_data[@]}")
      key_num="${#array_group_key_data_header[*]}"   # 列数の数
      # top_flg=0 は while の終わりで
    else
      #-----------------------
      # msel で使用する学習用データの行選択条件
      #-----------------------
      row_expression=""
      top=1
      for j in `seq 0 $((${key_num}-1))`; do
         if [ ${top} = 1 ]; then
           row_expression='$s{'${array_group_key_data_header[$j]%\%*}'}=="'${array_group_key_data[$j]}'"'
           top=0
         else
           row_expression=${row_expression}' && ''$s{'${array_group_key_data_header[$j]%\%*}'}=="'${array_group_key_data[$j]}'"'
         fi
      done # end of j 1つのグループ処理
      #-----------------------
      # 機械学習
      #-----------------------
      # 注意：msel c= の後で改行しないと 動作せず 実行時エラーになる  原因不明
      msel c="${row_expression}" \
           i=${tmp_input_file} |
      mcut f=${col_expression} > ${tmp_training_data}


      model_data_name=""
      logic_file_name=""    # 例 .../kdt.py → kdt を抽出

      for i in "${!array_command_list[@]}"; do
        logic_file_name=${array_command_list[$i]##*/}
        logic_file_name=${logic_file_name%.*}

        model_data_name=${model_data_path}/${array_command_list[$i]##*/}
        model_data_name=${model_data_name%.*}
    #echo ${array_command_list[$i]}
        python3 preprocess/selecttargetcolumn.py -t ${array_target_list[0]} -i ${tmp_training_data} |
        ${array_command_list[$i]} > ${model_data_name}


        #-----------------------
        # 予測値   ＜＜分類時 kcmd エラー発生するため 未実装＞＞
        #-----------------------
        if [[ -n ${output_predict_data} ]]; then
          :
        # kcmdエラーで予測がうまくできない
#          python postprocess/predict.py -d ${tmp_training_data} -i ${model_data_name}
        fi

        # 学習精度評価データの識別情報列の作成
        # msetstr の使用するため、mcmd形式で項目名リストと対応する値リスクを作成する
        evaluate_base_fld_name=""
        evaluate_base_fld_value=""
        declare -a array_fld_tmp=()
        declare -a array_val_tmp=()

        #-----------------------
        # データ件数   DATA_NUM        ＜＜未実装＞＞
        #-----------------------

        # 集計キー項目列
        for k in "${!array_group_key_list[@]}"; do
          array_fld_tmp+=( ${array_group_key_list[$k]} )
          array_val_tmp+=( ${array_group_key_data[$k]} )
        done

        # モデル化タイプ列  model_type_fld_name
        array_fld_tmp+=( ${MODEL_TYPE_FLD_NAME} )
        if [[ -n ${classification} ]]; then
          array_val_tmp+=( ${MODEL_TYPE_FLD_VAL_CLSSIFICATION} )
        else
          array_val_tmp+=( ${MODEL_TYPE_FLD_VAL_REGRESSION} )
        fi

        # 目的変数項目名リスト  TARGET_FLD_BASE_NAME
        for k in "${!array_target_list[@]}"; do
          if [ $k = 0 ]; then
            array_fld_tmp+=( ${TARGET_FLD_BASE_NAME} )
            array_val_tmp+=( ${array_target_list[0]} )
          else
            array_fld_tmp+=( ${TARGET_FLD_BASE_NAME}_$((k+2)) )
            array_val_tmp+=( ${array_target_list[$k]} )
          fi
        done

        # 特徴量項目名リスト  FEATURE_NAME
        array_fld_tmp+=( ${FEATURE_NAME} )
        tmp_fld_list=""
        for k in "${!array_feature_list[@]}"; do
          if [ $k = 0 ]; then
            tmp_fld_list=${array_feature_list[0]}
          else
            tmp_fld_list=${tmp_fld_list}'|'${array_feature_list[$k]}
          fi
        done
        array_val_tmp+=( "${tmp_fld_list}" )

        # 特徴量の数  FEATURE_NUM
        array_fld_tmp+=( ${FEATURE_NUM} )
        array_val_tmp+=( ${#array_feature_list[*]} )

        # ロジック名 logic_file_name
        array_fld_tmp+=( ${LOGIC_NAME} )
        array_val_tmp+=( ${logic_file_name} )

        #-----------------------
        # ロジックのパラメータ  LOGIC_PARM_NAME  ＜＜未実装＞＞
        #-----------------------
        # 現状 取得困難なため値を出力しない
#        array_fld_tmp+=( ${LOGIC_PARM_NAME} )
#        array_val_tmp+=( "" #注意 未実装 )


        # 列追加式
        top=1
        for k in "${!array_fld_tmp[@]}"; do
          if [ $top = 1 ]; then
            evaluate_base_fld_name=${array_fld_tmp[0]}
            evaluate_base_fld_value=${array_val_tmp[0]}
            top=0
          else
            evaluate_base_fld_name=${evaluate_base_fld_name}','${array_fld_tmp[$k]}
            evaluate_base_fld_value=${evaluate_base_fld_value}','${array_val_tmp[$k]}
          fi
        done

        # 学習精度評価
        # 暫定で 1評価指標 1実数 のもののみ対応

        if [ ${top_output_head} = 0 ]; then
          out_header="-nfno"
        else
          out_header=""
          top_output_head=0
        fi

        for j in "${!array_metrics_list[@]}"; do
          if [[ $j -gt 0 ]]; then
            out_header="-nfno"
          fi
          python3 postprocess/evaluate.py \
              -d ${tmp_training_data} \
              -i ${model_data_name} \
              -m ${array_metrics_list[$j]} |
          msetstr a=${METRICS_NAME} v=${array_metrics_list[$j]} |
          mcal    a=${METRICS_VALUE} c='$s{0}' -x |
          mcut    f=0 -r -x |
          msetstr a=${evaluate_base_fld_name} \
                  v=${evaluate_base_fld_value} ${out_header} |
mbest   size=1 -q >> ${tmp_output_metrics_data}
#注意 mbest は、evaluate.py 出力行数が開発時から増加したためと思われる重複行が出現するため追加
        done

      done
    fi # end of 先頭 or 先頭以外の処理
    top_flg=0
  done  < ${tmp_group_key_data}   # end of while グループ別
fi # end of グループ処理 あり





#後処理
rm -f ${tmp_group_key_data}
rm -f ${tmp_training_data}
exit 0
