# download MSG from MS storage account

# you need to install AzCopy
# sudo apt-get update; sudo apt-get install azcopy
# https://docs.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-linux?toc=%2fazure%2fstorage%2ftables%2ftoc.json#alternative-installation-on-ubuntu

VERSION="2019-01-01"
KEY="bsynHW1UiWhFgXKT95ISSFBOyrTJqnBW/WCayqATwHY2luq88CmVFa5rm92Ps6SH8PAnYu+/7rxu4dTJ7IYGAw=="

echo "getting graph version $VERSION"
array=(
    "ConferenceInstances.txt"
    "ConferenceSeries.txt"
    "FieldsOfStudy.txt"
    "Journals.txt"
    "Affiliations.txt"
    "PaperAuthorAffiliations.txt"
    "PaperReferences.txt"
    "Papers.txt"
    "Authors.txt"
)
for FILE in "${array[@]}"
do
    if [ "$FILE" ]; then
        echo azcopy --source https://academicgraph2.blob.core.windows.net/mag-$VERSION/mag/$FILE --destination graph/$VERSION/$FILE
        azcopy --source https://academicgraph2.blob.core.windows.net/mag-$VERSION/mag/$FILE --destination graph/$VERSION/$FILE --source-key $KEY
    fi
done

adv_array=(
    "FieldOfStudyChildren.txt"
    "PaperFieldsOfStudy.txt"
    "PaperRecommendations.txt"
    "RelatedFieldOfStudy.txt"
)
for FILE in "${adv_array[@]}"
do
    if [ "$FILE" ]; then
        echo azcopy --source https://academicgraph2.blob.core.windows.net/mag-$VERSION/advanced/$FILE --destination graph/$VERSION/$FILE
        azcopy --source https://academicgraph2.blob.core.windows.net/mag-$VERSION/advanced/$FILE --destination graph/$VERSION/$FILE --source-key $KEY
    fi
done
