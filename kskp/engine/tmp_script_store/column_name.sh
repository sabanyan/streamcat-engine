#!/bin/bash -eu
readonly  PROGNAME=$(basename $0 .sh)   # フォルダ名、拡張子を除いたファイル名
readonly  VERSION="0.0"

#注意

#外部モジュール参照
# awk
#--------------------------------------------------------------
# column_name
#--------------------------------------------------------------
function usage() {
    echo "${PROGNAME} ： 項目順の変更"
    echo "==========="
    echo " 先頭と末尾に、指定した項目名の順番に列を並び替える。"
    echo " NYSOL MCMDとの併用を想定し、"
    echo " 項目名への末尾に付加される特殊文字 %数字 についても対応"
    echo
    echo " f= 先頭、末尾に配置したい項目名を指定する"
    echo "    例 f=a,b,*,c,d"
    echo "    ＊：ワイルドカードは、明示的に指定した項目名を除いた残りの項目名を、"
    echo "       元の項目名の順序で展開する"
    echo "   補足：存在しない項目名は無視され、"
    echo "        ＊や同一項目名の複数回指定ある場合は、2回目以降は無視される"
    echo " i= 入力ファイル名を指定する。省略時は、標準入力を処理する"
    echo " o= 出力ファイル名を指定する。省略時は、標準出力へ書き込む"
    echo
    echo "書式"
    echo "------"
    echo "${PROGNAME} f= [i=] [o=] [--help] [--version]"
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
#   awk への -v 引数渡し の記述簡略化 のため
#   デフォルトが null or 0 となるようにする

exp_str=""        # f=
input_file=""
output_file=""

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
        'f='* )
            p_value=${1#*'='}                 # =より前の文字を削除
            if [[ -z "${p_value}" ]] ; then   # -z: 文字列長がゼロ
                echo "${PROGNAME}: option requires an argument -- $1" 1>&2
                exit 1
            fi
            exp_str=${p_value}
            shift 1
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

#必須パラメータの指定無しのチェック
if [[ -z ${exp_str} ]]; then
    echo "$PROGNAME: specify f= argument" 1>&2
    echo "Try '$PROGNAME --help' for more information." 1>&2
    exit 1
fi


# 準備処理
# i= 指定が無い場合、標準入力をセットする
if [[ -z ${input_file} ]]; then
  input_file='/dev/stdin'
fi

# o= 指定が無い場合、標準出力をセットする
if [[ -z ${output_file} ]]; then
  output_file='/dev/stdout'
fi

# データ処理
awk -v f="${exp_str}" \
'BEGIN{
  FS=","; OFS=",";
} # end of BEGIN
function is_fldname(list,fld) {
  for (tt in list) {
    if (tt == fld) {
      return 1;
      break;
    }
  } # end of for tt
  return 0;
} # end of func
{
  if (NR==1) {
    # colno 列名からの列番号参照用 配列
    for (i=1; i<=NF; i++) {
      # %数字チェックし 存在する場合、%数字 を削除
      fld_name = $i;
      sub(/%[0-9]+$/, "", fld_name);
      colno[fld_name] = i;
      colno_tmp[fld_name] = i;
    }
    # 先頭指定  head[1..]      連番
    # 末尾指定  tail[1..]      連番
    # その他    other[列順..]  元の列番号 を保持

    n = split( f, tmp, FS); # tmp f=指定のパース結果
    wc = 0;   # *出現フラグ
    k=0; l=0;
    for (i=1; i<=n; i++) {
      if ( tmp[i] == "*" ) {
        wc = 1;
      } else {
        if (wc == 0) {
          if (is_fldname(colno,tmp[i]) == 1) {
            head[++k] = tmp[i];
            head_name[tmp[1]] += 1;
          }
        } else {
          if (is_fldname(colno,tmp[i]) == 1 && is_fldname(head_name,tmp[i]) == 0) {
            tail[++l] = tmp[i];
          }
        }
      }
    } # end of for i

    # ワイルドカードの展開
    for (i in head) {
      delete colno_tmp[ head[i] ];
      }
    for (i in tail) {
      delete colno_tmp[ tail[i] ];
      }

    #
    m=0;
    for (ii=1; ii<=k; ii++) {
      newheader[++m] = colno[ head[ii] ];
      }

    for (ii=1; ii<=NF; ii++) {
      for (j in colno_tmp) {
        if ($ii == j) {
          newheader[++m] = ii;
          }
        } # end of for j
      } # end of for ii

    for (ii=1; ii<=l; ii++) {
      newheader[++m] = colno[ tail[ii] ];
      }
  } # end of if NR==1

  # データ出力
  for (i=1; i<=m; i++) {
    printf "%s", $newheader[i];
    if ( i<m ) {
      printf ",";
      }
    } # end of for i
  printf "\n"
}
' ${input_file} > "${output_file}"

exit 0
