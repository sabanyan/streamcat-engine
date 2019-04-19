#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.4"

#外部モジュール参照
# MCMD使用

# 注意・残件
#   ・空白含む項目名ある場合の挙動、未検証 ※恐らく意図通りにならない
# ver.0.4   k= 指定ない場合にエラーになる不具合を修正 (2019.2.25)
# ver.0.3   高速化のために、mcutで不要な項目を除外するように変更
#
#--------------------------------------------------------------
# groupby
#--------------------------------------------------------------
# NYSOL版 Group by 相当処理   横型データの作成方針
# 引数として与えらた変数
#    k=              集計キー項目をカンマ区切りで与える
#                    変数：key_list
#    f= sensor_list 同じ統計量計算を行う対象とする列範囲の指定  形式  入力データの列名をカンマ区切りで与える
#    c= feature_list NYSOLの統計量の指定と算出結果の列名の指定  形式  演算の指定:作成列名 をカンマ区切りで与える
#    [i=]            入力ファイル名を指定する。省略時は、標準入力を処理する
#                    変数：input_file      入力ファイル名
#    [o=]            出力ファイル名を指定する。省略時は、標準出力へ書き込む
#    [-q]            指定した場合、集計キー項目でソートをしない
#                    注意：予めソート
#    [-nfno]         項目名行を出力しない場合に指定する
#                    No Field Names for Output
#                    変数：header_output   ヘッダー行の出力要否   コマンド引数 -nfno より値をセットする
#                     ON   ヘッダー行を出力
#                     OFF  ヘッダー行を出力しない
#    [delimiter=]    センサー名と特徴量名との区切り文字。 省略時は _
#    [-prefix]     センサー名と特徴量名との連結方法を、接頭辞型にする。 省略時は、接尾型
#
# 処理の流れ
#   msortf      集計キー項目でソート
#   msummary    出力：複数項目を対象とした場合、統計量列は、横型
#   <Option>    横型の列項目の演算による列追加したい場合は、ここに記述する
#   m2cross     出力：統計量列を、縦型へ変換  ※全ての統計量を縦型データにする
#   mcal        出力：全ての統計量を識別する名前を値とする列を追加
#   mcross      出力：縦型の全ての統計量を、mcalで作成した列名で、列方向へ展開
#   mcut        mcrosが自動作成する不要なfld列を除外
#--------------------------------------------------------------
function usage() {
    echo "${PROGNAME} ： グループ別統計量算出"
    echo "==========="
    echo "  NYSOL MCMDを用いて、複数項目による集計において、"
    echo "  複数の数値列に対して、複数の統計量を適用した結果を、数値列名と統計量名からなる列名として出力する。"
    echo
    echo "  k= カンマ区切りで与えた列名リストを、集計の項目列とし、"
    echo "  f=  カンマ区切りで与えた列名リストを、集計対象とする数値項目列とし、"
    echo "  c= カンマ区切りで与えた集計で適用する統計量と結果に付加する接辞の指定より、"
    echo "  集計項目列でユニーク化したレコードに、数値項目列 × 統計量 の全ての組合せの演算結果を列とした結果を出力する。"
    echo
    echo "  演算子は、NYSOL 統計量リスト を指定することが可能"
    echo
    echo "  k=            集計のキー項目がある場合、項目名をカンマ区切りで指定する"
    echo "                例 k=A,B"
    echo "  f=            集計対象とする数値項目を、カンマ区切りで指定する"
    echo "                例 f=S1,S2"
    echo "  c=            適用する統計量と、対象項目名へ付加する接辞語を指定する"
    echo "                例 c=mean:Ave,count:Num,sum:Sum"
    echo "  -q            集計のキー項目でソート済の場合に指定するとソートしない分高速化する"
    echo "  -prefix       接辞語を、項目名の末尾ではなく、先頭に付加する"
    echo "  delimiter=    項目名と接辞語との区切り文字を指定する"
    echo "                デフォルトは _"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} [k=] f= c= [i=] [o=] [-q] [-nfno]"
    echo " [delimiter=] [-prefix]"
    echo " [-assert_diffSize] [-assert_nullkey] [-assert_nullin] [-assert_nullout]"
    echo " [tmpPath=] [precision=] [--help] [--version]"
    echo
    echo "例"
    echo "${PROGNAME} k=KA,KB f=A,B c=count:Num,mean:Avg"
    echo "出力の列名  KA,KB,A_Avg,A_Num,B_Avg,B_Num"

    exit 1
}

# エラー処理
set -e -u -o pipefail   # パイプ処理中にエラー発生で処理を終了する設定

error(){
  echo "#ERROR# Stoped ${PROGNAME}"
  echo "[ ${BASH_SOURCE} : ${LINENO} ] returns not zero status"
  exit 1
}

trap error ERR

# 引数の格納用変数、デフォルト値のセット
key_columns="ON"
header_output="ON"
no_sort=""
input_file=""
output_file=""
key_list=""
sensor_name=""
sensor_list=""
feature_list=""
feature_list_2=""
tmp_path=""
assert_diffSize=""
assert_nullkey=""
assert_nullin=""
assert_nullout=""
precision=""
delimiter="_"
prefix=false


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
        '-assert_nullkey' )
            assert_nullkey="-assert_nullkey"
            shift 1
            ;;
        '-assert_nullin' )
            assert_nullin="-assert_nullin"
            shift 1
            ;;
        '-assert_nullout' )
            assert_nullout="-assert_nullout"
            shift 1
            ;;
        '-assert_diffSize' )
            assert_diffSize="-assert_diffSize"
            shift 1
            ;;
        'tmpPath='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            tmp_path=${p_value}
            shift 1
            ;;
        'precision='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            precision=${p_value}
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
        'o='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            output_file=${p_value}
            shift 1
            ;;
        'k='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            key_list=${p_value}
            shift 1
            ;;
        'f='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            sensor_list=${p_value}
            shift 1
            ;;
        'c='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            feature_list=${p_value}
            shift 1
            ;;
        '-q' )
            no_sort="ON"
            shift 1
            ;;
        '-nfno' )
            header_output="OFF"
            shift 1
            ;;
        'delimiter='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            delimiter=${p_value}
            shift 1
            ;;
        '-prefix' )
            prefix=true
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

# 必須パラメータ指定無し
if [[ -z ${sensor_list} ]]; then  # f=
    echo "$PROGNAME: specify f= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi
if [[ -z ${feature_list} ]]; then  # c=
    echo "$PROGNAME: specify c= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi

# feature_list_2  feature_listの指定によりmsummaryで作成された列名をカンマ区切りで与えたリスト
feature_list_2=""
top_flg=1
for k in ${feature_list//,/ }; do
  if [ ${top_flg} = 1 ]; then
    feature_list_2="${k#*:}"
    top_flg=0
  else
    feature_list_2="${feature_list_2},${k#*:}"
  fi
done

readonly SENSOR_NAME='_sensor_name_'          # 同じ統計量計算を行う対象とする列範囲の指定で、それらを意味する概念的な項目名 ※テンポラリで最終出力には含まれない
readonly VAR_NAME='_var_name_'                # 全て縦型に変換する時の 統計量の名前を保持する列名を意味 ※テンポラリで最終出力には含まれない
readonly VALUE_NAME='_value_name_'            #     〃              統計量の値を保持する列名を意味  ※テンポラリで最終出力には含まれない
readonly UNIQUE_VAR_NAME='_unique_var_name_'  # group byで集計された列名 を保持するための列名を意味  ※テンポラリで最終出力には含まれない
readonly KEY_VALUE_LIST='KEY_VALUE_LIST'      # 集計キーの値を     空白区切りのベクトルで出力する 列名
readonly KEY_NAME_LIST='KEY_NAME_LIST'        # 集計キーの項目名を          〃
readonly key_name_char='"'${key_list//,/\",\"}'"'      # a,b,c 形式から "a","b","c" 形式へ変換   補足：mcal cat() で使用
readonly key_value_char='$s{'${key_list//,/'},$s{'}'}' # a,b,c 形式から $s{a},$s{b},$s{c} 形式へ変換   補足：mcal cat() で使用

# i= 指定が無い場合、標準入力をセットする
if [[ -z ${input_file} ]]; then
  input_file='/dev/stdin'
fi

# o= 指定が無い場合、標準出力をセットする
if [[ -z ${output_file} ]]; then
  output_file='/dev/stdout'
fi

# ヘッダー行出力の指定
header=""
if [ ${header_output} == "OFF" ]; then
  header="-nfno"
else
  header=""
fi

# tmpPath=
if [[ -n ${tmp_path} ]]; then
  tmp_path='tmpPath='${tmp_path}
fi

# precision=
if [[ -n ${precision} ]]; then
  precision='precision='${precision}
fi

# -k オプション指定
k_opt=""
k_opt_2=""
columns=""  # k= f= の列名リストを格納する
if [[ -n ${key_list} ]]; then
  k_opt="k=${key_list}"
  k_opt_2="k=${key_list},${SENSOR_NAME}"
  columns="${key_list},${sensor_list}"
else
  k_opt_2="k=${SENSOR_NAME}"
  columns="${sensor_list}"
fi

# センサー名、特徴量名、区切り文字からの列名作成指示
sensor_feature_name=""
if [[ "${prefix}" = true ]]; then
  sensor_feature_name='cat("'${delimiter}'",$s{'${VAR_NAME}'},$s{'${SENSOR_NAME}'})'
else
  sensor_feature_name='cat("'${delimiter}'",$s{'${SENSOR_NAME}'},$s{'${VAR_NAME}'})'
fi

# -q オプション
q_opt=""
if [[ -n ${no_sort} ]]; then
  q_opt='-q'
fi

# echo "columns=${columns}"
# echo "k_opt=${k_opt}"
# echo "sensor_list=${sensor_list}"
# echo "feature_list=${feature_list}"
# echo "feature_list_2=${feature_list_2}"
# echo "sensor_feature_name=${sensor_feature_name}"

  mcut     i=${input_file} \
           f="${columns}"  |
  msummary ${q_opt} ${k_opt} \
           f=${sensor_list} \
           c=${feature_list}  \
           a=${SENSOR_NAME} ${tmp_path} ${assert_nullkey} ${assert_nullin} ${assert_nullout} ${precision} |
  m2cross  ${k_opt_2} \
           f=${feature_list_2} \
           a=${VAR_NAME},${VALUE_NAME} ${tmp_path} ${assert_nullkey} ${assert_nullin} ${assert_nullout} |
  mcal     a=${UNIQUE_VAR_NAME} \
           c=${sensor_feature_name} ${assert_diffSize} ${tmp_path} ${assert_nullkey} ${assert_nullin} ${assert_nullout} ${precision} |
  mcross   ${k_opt} \
           f=${VALUE_NAME} \
           s=${UNIQUE_VAR_NAME} ${tmp_path} ${assert_nullkey} ${assert_nullin} ${assert_nullout} |
# -nfno
 if [[ -z ${header_output} ]]; then
   mcut     f=fld -r ${header} ${tmp_path} ${assert_diffSize} | \
   mfldname f=* -q ${header} o=${output_file}
 else
   mcut     f=fld -r ${header} ${tmp_path} ${assert_diffSize} \
            o=${output_file}
 fi


exit 0
