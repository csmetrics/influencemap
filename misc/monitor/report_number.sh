#!/bin/bash
ES_ADDR=http://130.56.248.105:9200
DIR=/mnt/influencemap/misc/monitor
WEBHOOK=https://www.cmlab.ml/hooks/fi1y5pxaztne5dj7demtpsihdo

cd $DIR
indices=("journals" "browse_author_group" "browse_paper_group" "conferenceinstances" \
         "fieldofstudychildren" "authors" "conferenceseries" "fieldsofstudy" \
         "paperauthoraffiliations" "papers" "paper_info" "paperreferences")

# set refresh_interval to 1s
for idx in "${indices[@]}"
do
    curl -XPUT $ES_ADDR/$idx/_settings -H 'Content-type: application/json' -d '{ "index": { "refresh_interval": "1s"  }}'
done
sleep 1m

# get the number of docs for each index
for idx in "${indices[@]}"
do
    mv counts/$idx.now.json counts/$idx.prev.json
    curl -XGET $ES_ADDR/$idx/_count > counts/$idx.now.json
done
python compare.py > output
sed -i "s/'/\"/g" output
curl -X POST -H 'Content-type: application/json' --data @output $WEBHOOK

# revert refresh_interval to -1
for idx in "${indices[@]}"
do
    curl -XPUT $ES_ADDR/$idx/_settings -H 'Content-type: application/json' -d '{ "index": { "refresh_interval": "-1"  }}'
done
