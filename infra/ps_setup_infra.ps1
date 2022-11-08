if ($args.count -lt 1) {
    Write-Output "No parameter passed. Please provide a suffix to guarantee uniqueness of resource names"
    exit
}

$SUFFIX = $args[0]
$RG_NAME = "data-share-automation"
$LOCATION = "westeurope"
$SOURCE_STORAGE_ACCOUNT_NAME = "sourcestorage$SUFFIX"
$DEST_STORAGE_ACCOUNT_NAME = "deststorage$SUFFIX"
$SOURCE_DATA_SHARE_ACCOUNT_NAME = "source-data-share$SUFFIX"
$DEST_DATA_SHARE_ACCOUNT_NAME = "dest-data-share$SUFFIX"
$CONTAINER_NAME = "share-data"

az group create -l $LOCATION -g $RG_NAME
az storage account create -l $LOCATION -g $RG_NAME -n $SOURCE_STORAGE_ACCOUNT_NAME --hns True --kind StorageV2
az storage account create -l $LOCATION -g $RG_NAME -n $DEST_STORAGE_ACCOUNT_NAME --hns True --kind StorageV2
az datashare account create -l $LOCATION -g $RG_NAME -n $SOURCE_DATA_SHARE_ACCOUNT_NAME
az datashare account create -l $LOCATION -g $RG_NAME -n $DEST_DATA_SHARE_ACCOUNT_NAME 

KEY=$(az storage account keys list -g $RG_NAME -n $SOURCE_STORAGE_ACCOUNT_NAME --query [0].value -o tsv)

az storage container create --account-name $SOURCE_STORAGE_ACCOUNT_NAME --account-key $KEY -n $CONTAINER_NAME
az storage blob upload --account-name $SOURCE_STORAGE_ACCOUNT_NAME --account-key $KEY --container $CONTAINER_NAME -f Readme.md --overwrite
