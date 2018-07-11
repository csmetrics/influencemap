import os,json

data_dir = "counts"
files = os.listdir(data_dir)
data_now = [f for f in files if f.split('.')[1] == "now"]

output = "|{}|{}|{}|\n".format("index", "changes", "total")
output += "|---:|---:|---:|\n"
# print("{:>25}\t{:>12}\t{:>12}".format("index", "changes", "total"))
for data in data_now:
    now = json.loads(open(os.path.join(data_dir, data)).read())
    prev = json.loads(open(os.path.join(data_dir, data.replace("now", "prev"))).read())
    output += "|*{}*| {:,}| {:,}|\n".format(data.split('.')[0], now["count"]-prev["count"], now["count"])
    # print("{:>25}\t{:>12,}\t{:>12,}".format(data.split('.')[0], now["count"]-prev["count"], now["count"]))
print({
    "text": output
})
