## How to run influencemap

(1) Clone repository and create environment
```
$ git clone [https://github.com/csmetrics/influencemap](https://github.com/csmetrics/influencemap)

$ conda create -n influence python=3
$ conda activate influence
```

(2) Build
```
$ cd influencemap
$ pip install -e .
```

(3) Edit ES server setting

graph/config.json
```json
"elasticsearch":{
    "hostname":"115.146.86.238:9200",
}, // this requires access to Elasticsearch
```

(4) Run
```
$ ./run.sh
```
