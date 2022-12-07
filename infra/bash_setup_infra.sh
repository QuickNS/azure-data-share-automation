#!/bin/bash

if [[ -z $1 ]];
then 
    echo "No parameter passed. Please provide a suffix to guarantee uniqueness of resource names"
    exit
fi

SUFFIX=$1
RG_NAME=data-share-automation
LOCATION=westeurope
SOURCE_STORAGE_ACCOUNT_NAME=sourcestorage$SUFFIX
DEST_STORAGE_ACCOUNT_NAME=deststorage$SUFFIX
SOURCE_DATA_SHARE_ACCOUNT_NAME=source-data-share$SUFFIX
DEST_DATA_SHARE_ACCOUNT_NAME=dest-data-share$SUFFIX
CONTAINER_NAME=share-data

echo "Creating resource group '$RG_NAME'"
az group create -l $LOCATION -g $RG_NAME -o none
echo "Creating source storage account '$SOURCE_STORAGE_ACCOUNT_NAME'"
az storage account create -l $LOCATION -g $RG_NAME -n $SOURCE_STORAGE_ACCOUNT_NAME --hns True --kind StorageV2 -o none
echo "Creating destination storage account '$DEST_STORAGE_ACCOUNT_NAME'"
az storage account create -l $LOCATION -g $RG_NAME -n $DEST_STORAGE_ACCOUNT_NAME --hns True --kind StorageV2 -o none
echo "Creating source data share account '$SOURCE_DATA_SHARE_ACCOUNT_NAME'"
az datashare account create -l $LOCATION -g $RG_NAME -n $SOURCE_DATA_SHARE_ACCOUNT_NAME -o none --only-show-errors
echo "Creating source data share account '$DEST_DATA_SHARE_ACCOUNT_NAME'"
az datashare account create -l $LOCATION -g $RG_NAME -n $DEST_DATA_SHARE_ACCOUNT_NAME -o none --only-show-errors

echo "Retrieving storage key to upload sample data..."
KEY=$(az storage account keys list -g $RG_NAME -n $SOURCE_STORAGE_ACCOUNT_NAME --query [0].value -o tsv)

echo "Creating container '$CONTAINER_NAME' in '$SOURCE_STORAGE_ACCOUNT_NAME'"
az storage container create --account-name $SOURCE_STORAGE_ACCOUNT_NAME --account-key $KEY -n $CONTAINER_NAME -o none
echo "Uploading data..."
az storage blob upload --account-name $SOURCE_STORAGE_ACCOUNT_NAME --account-key $KEY --container $CONTAINER_NAME -f Readme.md --overwrite -o none --only-show-errors
echo "All Done!"