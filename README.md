## 1. 概要

StreamCatは、オープンソースとして公開するデータ分析プラットフォームです

<img alt="streamcat_demo" src="https://user-images.githubusercontent.com/93304382/154427837-0ffc301a-9932-4773-abe7-4b2847c76c74.gif" width="48%">

## 2. 動作環境

StreamCatは、[Docker](https://ja.wikipedia.org/wiki/Docker)上で動作するWebアプリケーションです。動作にはDockerが必要です。

|Windows|[Docker Desktop](https://www.docker.com/get-started)|
|:-:|:-|
|**macOS**|[**Docker Desktop**](https://www.docker.com/get-started)|
|**Linux**|[**Docker Engine**](https://docs.docker.com/engine/), [**Docker Compose**](https://docs.docker.com/compose/)|


## 3. インストール

### 1. Dockerコンテナの取得と起動

1. [`streamcat.zip`](https://github.com/sabanyan/community/files/10799071/streamcat.zip)をダウンロードする

2. 以下のコマンドを上から順に実行する

    ```sh
    # 1. zipファイルを解凍する
    unzip streamcat.zip

    # 2. streamcatディレクトリに移動する
    cd streamcat

    # 3. StreamCatサーバを起動する (最新のStreamCatイメージがダウンロードされ、StreamCatサーバが起動する)
    docker compose up -d
    ```

### 2. 起動確認

Webブラウザ(ChromeまたはFirefoxを推奨)で[`http://localhost:5000`](http://localhost:5000)にアクセスして、以下のログイン画面が表示されればインストール完了です。

<img alt="streamcat_login" src="https://user-images.githubusercontent.com/93304382/154427880-1a7dfd82-71e7-4660-a8fa-8ee836eae458.png" width="48%">

### 3. 利用開始

ログイン画面から以下のアカウントでログインします。

|ユーザーアカウント|`admin@streamcat.io`|
|:-|:-|
|**パスワード**|`adminpass0`|

初回ログイン時にはパスワードの変更を求められます。
パスワードを変更してください。変更後のパスワードは次回以降のログイン時に必要なので忘れないようにして下さい。

### 4. 利用方法

公式マニュアルを準備中です


## 4. アンインストール
以下のコマンドを上から順に実行して下さい
```sh
# 1. Dockerコンテナの停止と削除
docker compose down

# 2. Dockerイメージの削除
docker rmi sabanyan/streamcat:latest
docker rmi postgres:15-alpine

# 3. Dokcer Volumeの削除
docker volume rm streamcat_files streamcat_meta

# 4. docker-compose.ymlを削除する
rm ./docker-compose.yml
```
