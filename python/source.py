from datetime import datetime
from pprint import pprint

from azure.identity import DefaultAzureCredential, AzureCliCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.datashare import DataShareManagementClient
from azure.mgmt.datashare.models import (
    ADLSGen2FileSystemDataSet,
    Invitation,
    ScheduledSynchronizationSetting,
    Share,
    ShareKind,
)
from dotenv import load_dotenv

# source data share settings
subscription_id = "<subscription-id>"
resource_group_name = "data-share-automation"
account_name = "source-data-sharexyz"
share_name = "TestShare"
dataset_name = "TestDataSet"
storage_account_name = "sourcestoragexyz"
file_system_name = "share-data"

# destination object for invitation
dest_tenant_id = "<destination_tenant_id>"
dest_object_id = "<destination_object_id>"

# destination email address
dest_email_address = None


def list_accounts():
    # list data shares in resource group
    print("\n### List Data Shares in Resource Group ###")
    result = client.accounts.list_by_resource_group(resource_group_name)
    for x in result:
        pprint(x.as_dict())


def get_account():
    # get data share account
    print("\n### Get Data Share ###")
    result = client.accounts.get(resource_group_name, account_name)
    pprint(result.as_dict())


def get_shares_in_account():
    # get shares in account
    print("\n### Get Shares in Account ###")
    result = client.shares.list_by_account(resource_group_name, account_name)
    for x in result:
        pprint(x.as_dict())


def create_share_in_account():
    # create share in account
    print("\n### Create Share in Account ###")
    share = Share(
        description="My Description",
        share_kind=ShareKind("CopyBased"),
        terms="My Terms",
    )
    result = client.shares.create(resource_group_name, account_name, share_name, share)
    pprint(result.as_dict())


def get_share():
    # get a share by name
    print("\n### Get Share by Name ###")
    result = client.shares.get(resource_group_name, account_name, share_name)
    pprint(result.as_dict())


def set_schedule():
    # set share schedule
    print("\n### Set Share Schedule ###")

    # check if exists
    try:
        sync_settings = client.synchronization_settings.get(
            resource_group_name,
            account_name,
            share_name,
            f"{share_name}-synchronization-settings",
        )
    except ResourceNotFoundError:
        sync_settings = None

    if sync_settings is None:
        settings = ScheduledSynchronizationSetting(
            recurrence_interval="Day", synchronization_time=datetime.now()
        )

        result = client.synchronization_settings.create(
            resource_group_name,
            account_name,
            share_name,
            f"{share_name}-synchronization-settings",
            settings,
        )
        pprint(result.as_dict())
    else:
        print("Schedule already exists")
        pprint(sync_settings.as_dict())


def create_dataset():
    # create dataset
    print("\n### Create Dataset ###")

    data_set = ADLSGen2FileSystemDataSet(
        file_system=file_system_name,
        subscription_id=subscription_id,
        resource_group=resource_group_name,
        storage_account_name=storage_account_name,
    )

    result = client.data_sets.create(
        resource_group_name, account_name, share_name, dataset_name, data_set
    )
    pprint(result.as_dict())


def get_dataset():
    # get dataset
    print("\n### Get Dataset ###")

    result = client.data_sets.get(
        resource_group_name, account_name, share_name, dataset_name
    )
    pprint(result.as_dict())


def create_invitation_by_email(invitation_name, email):
    # create invitation
    print("\n### Create Invitation ###")
    invitation = Invitation(target_email=email)
    result = client.invitations.create(
        resource_group_name,
        account_name,
        share_name,
        invitation_name,
        invitation,
    )
    print(result.as_dict())


def create_invitation_by_target_id(invitation_name, tenant_id, client_id):
    # create invitation
    print("\n### Create Invitation ###")
    invitation = Invitation(
        target_active_directory_id=tenant_id, target_object_id=client_id
    )
    result = client.invitations.create(
        resource_group_name,
        account_name,
        share_name,
        invitation_name,
        invitation,
    )
    print(result.as_dict())


def get_invitations():
    # get invitations
    print("\n### Get Invitations ###")
    result = client.invitations.list_by_share(
        resource_group_name, account_name, share_name
    )
    invitations = list()
    for x in result:
        pprint(x.as_dict())
        invitations.append(x.as_dict())
    return invitations


def get_invitation_by_name(invitation_name):
    # get invitations
    print("\n### Get Invitation by Id ###")
    result = client.invitations.get(
        resource_group_name, account_name, share_name, invitation_name
    )
    pprint(result.as_dict())


# Execution starts here

# load .env file (if any)
load_dotenv("source.env")

# login with AZ CLI credentials to setup data share and create invitation
cred = DefaultAzureCredential(exclude_visual_studio_code_credential=True)

# create client
client = DataShareManagementClient(cred, subscription_id)

# create source share
create_share_in_account()
# create dataset
create_dataset()
# create schedule
set_schedule()
# send invitation
if dest_email_address is not None:
    create_invitation_by_email("test-inv-email", dest_email_address)

create_invitation_by_target_id(
    invitation_name="test-sp",
    tenant_id=dest_tenant_id,
    client_id=dest_object_id,
)
