from pprint import pprint

from azure.identity import DefaultAzureCredential
from azure.mgmt.datashare import DataShareManagementClient
from azure.mgmt.datashare.models import (
    ADLSGen2FileSystemDataSetMapping,
    ShareSubscription,
)
from dotenv import load_dotenv

# destination data share settings
subscription_id = "<subscription-id>"
account_name = "dest-data-sharexyz"
resource_group_name = "data-share-automation"
dest_storage_account_name = "deststoragexyz"


def get_consumer_invitations(client: DataShareManagementClient):
    # get consumer invitations
    print("\n### Get Consumer Invitations ###")
    result = client.consumer_invitations.list_invitations()
    invitations = list()
    for x in result:
        pprint(x.as_dict())
        invitations.append(x.as_dict())
    return invitations


def create_share_subscription(
    client: DataShareManagementClient, invitation_id: str, subscription_name: str
):
    # create share subscription
    print(f"\n### Create Share Subscription for invitation {invitation_id} ###")
    subscription = ShareSubscription(
        invitation_id=invitation_id, source_share_location="westeurope"
    )
    result = client.share_subscriptions.create(
        resource_group_name, account_name, subscription_name, subscription
    )
    pprint(result.as_dict())
    return result


def get_consumer_source_datasets(
    client: DataShareManagementClient, subscription_name: str
):
    # get source datasets
    print("\n### Get Consumer Source Datasets ###")
    result = client.consumer_source_data_sets.list_by_share_subscription(
        resource_group_name, account_name, subscription_name
    )
    data_sets = list()
    for x in result:
        pprint(x.as_dict())
        data_sets.append(x.as_dict())
    return data_sets


def create_dataset_mapping(
    client: DataShareManagementClient,
    subscription_name: str,
    dataset_id: str,
    dataset_path: str,
):
    # create dataset mapping
    print("\n### Create Dataset mappings ###")
    data_set_mapping = ADLSGen2FileSystemDataSetMapping(
        data_set_id=dataset_id,
        file_system=dataset_path,
        subscription_id=subscription_id,
        resource_group=resource_group_name,
        storage_account_name=dest_storage_account_name,
    )
    result = client.data_set_mappings.create(
        resource_group_name,
        account_name,
        subscription_name,
        f"{dataset_path}-dataset-mapping",
        data_set_mapping,
    )
    pprint(result.as_dict())


def get_subscription_synchronization_setting(
    client: DataShareManagementClient, subscription_name: str
):
    # get synchronization settings
    print("\n### Get Synchronization Setting ###")
    result = client.share_subscriptions.list_source_share_synchronization_settings(
        resource_group_name, account_name, subscription_name
    )

    for x in result:
        # just get the first
        print(x.as_dict())
        return x


def create_trigger(
    client: DataShareManagementClient, subscription_name: str, trigger: str
):
    # create trigger
    print("\n### Create Trigger ###")
    result = client.triggers.begin_create(
        resource_group_name,
        account_name,
        subscription_name,
        f"{subscription_name}-trigger",
        trigger,
    )
    pprint(result.result().as_dict())


def main():
    # Execution starts here

    # load .env file (if any)
    load_dotenv("dest.env")

    # use az login credentials
    cred = DefaultAzureCredential()

    client = DataShareManagementClient(cred, subscription_id)

    # accept invitation in the context of the current AZ CLI user
    invitations = get_consumer_invitations(client)

    if invitations is None or len(invitations) == 0:
        print("No invitations found for this identity")
    else:
        for invitation in invitations:
            invitation_id = invitation["invitation_id"]
            # set a subscription name - we will use the name of the original share
            subscription_name = f"Subscription_{invitation['share_name']}"
            create_share_subscription(client, invitation_id, subscription_name)

            # create mapping
            datasets = get_consumer_source_datasets(client, subscription_name)
            for dataset in datasets:
                dataset_id = dataset["data_set_id"]
                dataset_name = dataset["data_set_path"]
                create_dataset_mapping(
                    client, subscription_name, dataset_id, dataset_name
                )

            # create trigger
            sync_setting = get_subscription_synchronization_setting(
                client, subscription_name
            )
            create_trigger(client, subscription_name, sync_setting)


if __name__ == "__main__":
    main()
