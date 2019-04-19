#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="1.0"

#外部モジュール参照
# awk

#未実装箇所

#--------------------------------------------------------------
# column_list
#--------------------------------------------------------------

function usage() {
    echo "${PROGNAME} ： 項目名リストの取得"
    echo "==========="
    echo " 項目名行とn=で指定したデータの行数を、縦型に変形したcsvデータを出力する"
    echo
    echo " n= 出力したいデータの行数を指定する。最大100行まで出力可能"
    echo "    デフォルトは0件で先頭行のみ。100行以上を指定した場合、100行までを出力"
    echo
    echo " -no   出力データの先頭列に連番を出力する"
    echo
    echo " -nfno 出力データの項目名行を出力しない(No Field Names for Outputの略)"
    echo
    echo " i= 入力ファイル名を指定する。省略時は、標準入力を処理する"
    echo " o= 出力ファイル名を指定する。省略時は、標準出力へ書き込む"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} [i=] [o=] [n=] [-no] [-nfno] [--help] [--version]"
    echo

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

# 引数格納用変数
input_file=""   # i=
output_file=""  # o=
n=0             # n=
no=""           # -no
nfno=""         # -nfno

# 参考 引数処理： https://qiita.com/b4b4r07/items/dcd6be0bb9c9185475bb
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
        'n='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            n=${p_value}
            shift 1
            ;;
        '-no')
            shift 1
            no=1
            ;;
        '-nfno')
            shift 1
            nfno=1
            ;;
        '--'|'-' )
            shift 1
            break
            ;;
        -*)
            echo "$PROGNAME: illegal option -- '$(echo $1 | sed 's/^-*//')'" 1>&2
            exit 1
            ;;
        *)
            if [[ ! -z "$1" ]] && [[ ! "$1" =~ ^-+ ]]; then
               shift 1
            fi
            ;;
    esac
done

# 必須パラメータ指定無し
# if [[ -z ${} ]]; then
#     echo "$PROGNAME: specify k= argument" 1>&2
#     echo "Try '$PROGNAME --help' for more information." 1>&2
#     exit 1
# fi

# 準備処理
# p= and f= 指定が無い場合、標準入力をセットする
if [[ -z ${input_file} ]]; then
  input_file='/dev/stdin'
fi

# o= 指定が無い場合、標準出力をセットする
if [[ -z ${output_file} ]]; then
  output_file='/dev/stdout'
fi

# 定数
readonly FIELD_NAME='FIELD_NAME'
readonly VALUE_NAME='VALUE'
readonly NO_NAME="NO"
readonly MAX_NUM=100  # n= で有効とする上限の行数

# データ処理
awk -v n="${n}" \
    -v no="${no}" \
    -v nfno="${nfno}" \
    -v FIELD_NAME="${FIELD_NAME}" \
    -v VALUE_NAME="${VALUE_NAME}" \
    -v NO_NAME="${NO_NAME}" \
    -v MAX_NUM="${MAX_NUM}" \
'BEGIN{
  FS=","; OFS=",";
  if (n >= MAX_NUM) {
    n = MAX_NUM
  }
  if (n < 0) {
    n = 0
  }
  max_NF = 0  # 最大列数のカウント
  max_NR = 0  # 実際の対象行数カウント
} # end of BEGIN
{
  # data[i,j]  i行 j列のデータを格納する
  if (max_NF <= NF) {max_NF = NF}
  if (NR <= n+1) {
    for (j=1; j<=NF; j++) {
        data[NR,j] = $j
    } # end of for jj
    max_NR = NR
  } else {
    exit
  }
}
END{
  # 行列を 転置して出力

  # -no処理  出力データの先頭列へ連番追加
  output_start_no = 1
  if (no != "") {
    for (j=1; j<=max_NF; j++) {
      data[0,j] = j
    }
    output_start_no = 0
  }

  # ヘッダー行の出力
  if (nfno == "") {
    if (no != "") { printf("%s,", NO_NAME) }
    printf("%s", FIELD_NAME)
    for (j=2; j<=max_NR; j++) {
      printf(",%s_%d", VALUE_NAME, j-1)
    }
    printf("\n")
  }

  # 値行の出力
  for (i=1; i<=max_NF; i++) {
    for (j=output_start_no; j<=max_NR; j++) {
        if (j != output_start_no) { printf(",")}
        printf("%s", data[j,i])
    }
    printf("\n")
  }
}
' ${input_file} > "${output_file}"

exit 0

# MCMD版 （旧版 廃止）
# msel      c='top()' \
#           i="${input_file}" | \
# msetstr   a=tmp v="a" | \
# mcross    f=* s=tmp | \
# msel      c='$s{fld}!="tmp"' | \
# mfldname  n="${FIELD_NAME}","${VALUE_NAME}" \
#           o="${output_file}"
