from pprint import pprint

from azure.identity import DefaultAzureCredential
from azure.mgmt.datashare import DataShareManagementClient
from azure.mgmt.datashare.models import (
    ADLSGen2FileSystemDataSetMapping,
    ShareSubscription,
)
from dotenv import load_dotenv

# destination data share settings
subscription_id = "<destination-subscription-id>"
account_name = "dest-data-sharexyz"
resource_group_name = "data-share-automation"
subscription_name = "TestSubscription"
dest_file_system_name = "shared-data"
dest_storage_account_name = "deststoragexyz"


def get_consumer_invitations():
    # get consumer invitations
    print("\n### Get Consumer Invitations ###")
    result = client.consumer_invitations.list_invitations()
    invitations = list()
    for x in result:
        pprint(x.as_dict())
        invitations.append(x.as_dict())
    return invitations


def get_consumer_invitation_by_id(invitation_id, region):
    # get consumer invitation by id
    print("\n### Get Consumer Invitations ###")
    result = client.consumer_invitations.get(region, invitation_id)
    pprint(result.as_dict())


def create_share_subscription(invitation_id):
    # create share subscription
    print(
        f"\n### Create Share Subscription for invitation {invitation_id} ###"
    )
    subscription = ShareSubscription(
        invitation_id=invitation_id, source_share_location="westeurope"
    )
    result = client.share_subscriptions.create(
        resource_group_name, account_name, subscription_name, subscription
    )
    pprint(result.as_dict())


def get_share_subscriptions():
    # get share subscription
    print("\n### Get Share Subscription ###")
    result = client.share_subscriptions.get(
        resource_group_name=resource_group_name,
        account_name=account_name,
        share_subscription_name=subscription_name,
    )
    pprint(result.as_dict())


def get_dataset_mappings(resource_group_name, account_name, share_name):
    # get dataset mappings
    print("\n### Get Dataset mappings ###")
    result = client.data_set_mappings.list_by_share_subscription(
        resource_group_name, account_name, share_name
    )
    for x in result:
        pprint(x.as_dict())


def get_consumer_source_datasets(share_subscription):
    # get source datasets
    print("\n### Get Consumer Source Datasets ###")
    result = client.consumer_source_data_sets.list_by_share_subscription(
        resource_group_name, account_name, share_subscription
    )
    data_sets = list()
    for x in result:
        pprint(x.as_dict())
        data_sets.append(x.as_dict())
    return data_sets


def create_dataset_mapping(dataset_id):
    # create dataset mapping
    print("\n### Create Dataset mappings ###")
    data_set_mapping = ADLSGen2FileSystemDataSetMapping(
        data_set_id=dataset_id,
        file_system=dest_file_system_name,
        subscription_id=subscription_id,
        resource_group=resource_group_name,
        storage_account_name=dest_storage_account_name,
    )
    result = client.data_set_mappings.create(
        resource_group_name,
        account_name,
        subscription_name,
        f"{subscription_name}-dataset-mapping",
        data_set_mapping,
    )
    pprint(result.as_dict())


def get_subscription_synchronization_setting():
    # get synchronization settings
    print("\n### Get Synchronization Setting ###")
    result = (
        client.share_subscriptions.list_source_share_synchronization_settings(
            resource_group_name, account_name, subscription_name
        )
    )

    for x in result:
        # just get the first
        print(x.as_dict())
        return x


def create_trigger(trigger):
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


load_dotenv(".env")

# use az login credentials
cred = DefaultAzureCredential()

client = DataShareManagementClient(cred, subscription_id)

# accept invitation in the context of the current AZ CLI user
result = get_consumer_invitations()

if result is None or len(result) == 0:
    print("No invitations found for this identity")
else:
    invitation_id = result[0]["invitation_id"]
    create_share_subscription(invitation_id)
    get_share_subscriptions()

    # create mapping
    result = get_consumer_source_datasets(subscription_name)
    data_set_id = result[0]["data_set_id"]
    create_dataset_mapping(data_set_id)

    # create trigger
    result = get_subscription_synchronization_setting()
    create_trigger(result)
