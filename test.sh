#!/use/bin/bash
tee >(nkf -s -Lw --cp932 > 'kskp/data/library/フロー実行キャッシュ/cache.csv' ) < 'kskp/data/cache_data.csv' > '/dev/stdout'
