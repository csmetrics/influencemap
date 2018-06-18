import os, sys, json
from pyhocon import ConfigFactory

conf = None
def get(key, default = None):
	try:
		global conf
		return conf.get(key, default)
	except AttributeError as aex:
		return default


mandatory_confs = [
	"elasticsearch.hostname",
	"data.filedir",
	"data.version"
]

conf = ConfigFactory.parse_file("config.json")
for key in mandatory_confs:
    assert key in conf, "Key %s down not exists" % key
