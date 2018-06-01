# you need to install Azure CLI 2.0
# https://docs.microsoft.com/en-us/azure/data-lake-store/data-lake-store-get-started-cli-2.0#rename-download-and-delete-data-from-a-data-lake-store-account
# [
#  {
#   "cloudName": "AzureCloud",
#   "id": "cb1d9878-3345-441a-9b1b-8110acd72aeb",
#   "isDefault": true,
#   "name": "Pay-As-You-Go",
#   "state": "Enabled",
#   "tenantId": "e37d725c-ab5c-4624-9ae5-f0533e486437",
#   "user": {
#     "name": "u1033719@anu.edu.au",
#     "type": "user"
#   }
#  }
#]

#az dls fs download --account academicgraph --source-path /graph/2018-04-13 --destination-path 2018-04-13

VERSION="2018-04-13"

echo "getting graph version $VERSION"
flist=`az dls fs list --account academicgraph --path /graph/$VERSION | python -c "import sys, json; print([f['name'] for f in json.load(sys.stdin)])"`
IFS="'[], " read -r -a array <<< "$flist"

for FILE in "${array[@]}"
do
    if [ "$FILE" ]; then
        echo az dls fs download --account academicgraph --source-path $FILE --destination-path $FILE
        az dls fs download --account academicgraph --source-path $FILE --destination-path $FILE
    fi
done


