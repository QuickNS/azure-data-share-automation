# Data Share Automation

## Description

[Azure Data Share](https://azure.microsoft.com/en-us/services/data-share/) setup requires a number of steps to establish the connection between the source data and the destination. One of those steps is sending an invitation from a source data share account and accepting the invitation in a destination data share account.

Through the portal UI, invitations can only be sent to email addresses and that requires the email recipient to perform some manual steps to accept the invitation and map the incoming data to the destination. However, the Azure Data Share SDK allows invitations to be sent to *service principals* as well, which opens up the opportunity to fully automate the process, even between different subscriptions and tenants.

This code illustrates how to perform a fully automated data sharing process between two pre-existing Data Share accounts. It includes two separate Python scripts:

### source.py

- Creates a share in a data share account
- Sets up a dataset from a ADLSGen2 storage account file system
- Creates a synchronization schedule for the share
- Sends out invitations to an email user and a service principal on a specific Azure AD tenant

### dest.py

- Lists invitations sent to the user
- Creates a subscription for a share
- Creates a mapping for the dataset that points to an ADLSGen2 storage account file system
- Enables the scheduling trigger

## Prerequisites

- A *source* Azure Data Share account
- A *destination* Azure Data Share account
- A *source* Azure Storage Data Lake account (Gen2)
- A *destination* Azure Storage Data Lake account (Gen2)

Alternatively, the infra folder includes bash and powershell scripts to setup these 4 assets in a new resource group. The scripts also create a container in the *source* storage account and upload this Readme.md file to it.

> Note: [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/) is required to execute these scripts.

### Bash

```bash
# login and make sure the right subscription is selected
az login
# setup infrastructure
./infra/bash_setup_infra.sh
```

### Powershell

```powershell
# login and make sure the right subscription is selected
az login
# setup infrastructure
./infra/ps_setup_infra.ps1
```

## Creating the service principal

To automate the acceptance of the invitation, a service principal must be created in the destination Azure AD tenant.

```bash
az ad sp create-for-rbac --name "<insert_sp_name>"
```

It will output something like this:

```json
{
  "appId": "b50dc79f-7120-46e6-8703-1ebdb0a5e66b",
  "displayName": "azure-data-share-test",
  "name": "b50dc79f-7120-46e6-8703-1ebdb0a5e66b",
  "password": "<generated-client-secret>",
  "tenant": "<your-tenant-id>"
}
```

The **appId**, **password** and **tenant** are required by the Python scripts.

Additionally, we need the **objectId** of the service principal, which can be obtained by running the following command:

```bash
az ad sp list --display-name <insert_sp_name> --query []."objectId" -o tsv
```

These values will be referenced in the scripts through environment variables:

- AZURE_CLIENT_ID: appId
- AZURE_CLIENT_SECRET: password
- AZURE_TENANT_ID: tenant

The objectId will be used in the `source.py` script as the target of the invitation.

## Role Assignments

- The **source** data share MSI must have the **Storage Blob Data Reader** role in the source storage account

    Example:
    ![add-data-share-permissions](./media/add-data-share-permissions.png)

- The **destination** data share MSI must have the **Storage Blob Data Contributor** role in the destination storage account.

## Sharing data

First we need to create the share, select the data we want to share and send an invitation. Those tasks are all automated in the `python\source.py` script.

### Configuration

In the `python/source.py` file, modify the following settings to match your configuration:

```python
# source data share settings
subscription_id = "<source-subscription-id>"
resource_group_name = "data-share-automation"
account_name = "source-data-sharexyz"
share_name = "TestShare"
dataset_name = "TestDataSet"
storage_account_name = "sourcestoragexyz"
file_system_name = "source-data"

# destination object for invitation
dest_tenant_id = "<destination_tenant_id>"
dest_object_id = "<destination_object_id>"

# destination email address
dest_email_address = None
```

Make sure you correctly configure the `dest_object_id` variable to the **objectId** of the service principal created earlier.

### Authentication

The source script uses the DefaultAzureCredential class for authenticating on Azure. It uses one of several authentication mechanisms:

- The EnvironmentCredential is the first method tried by the DefaultAzureCredential class. It will look for the environment variables AZURE_CLIENT_ID, AZURE_SECRET_ID and AZURE_TENANT_ID

- It they aren't set, it will try to use Managed Identities which will be available in a hosting environment such as Azure App Service.

- If not present, it will try AZ CLI login credentials, provided az login command is ran before using it.
This is a simple way of running the script under your Azure account identity (and if you created the assets yourself, you should already have all the required permissions and roles over the resources)

The identity running the script must have the following permissions:

*Source* Data Share Account:

- **Contributor**

*Source* Storage Account:

- **Contributor**
- **User Access Administrator**

The simplest process is to run the script using your AZ CLI credentials which requires no setup.

However, if you do want to run in the context of a service principal account, you should create a `.env` file in the `python` folder and add the following values:

```env
AZURE_CLIENT_ID=client_id
AZURE_CLIENT_SECRET=client_secret
AZURE_TENANT_ID=tenant_id
```

The script is prepared to read this file if it exists and will default to using service principal credentials.

### Running

Execute the following commands:

```bash
cd python
pip install -r requirements.txt

# if using az cli credentials
az login

python source.py
```

The script should be indempotent so you can run it multiple times. As a result, you should see a share created in your *source* data share account:

![data_share_created](./media/share_created.png)

A schedule should be configured on the share:

![schedule](./media/schedule.png)

A dataset should be configured and mapped to the storage account container:

![dataset](./media/dataset.png)

Finally, an invitation should exist for the service principal:

![invitation](./media/invitation.png)

## Receiving data

Now, we need to accept the sent invitation, map the incoming data to the destination storage account and setup the schedule. Those tasks are automated in the `python\dest.py` script.

### Configuration

In the `python/source.py` file, modify the following settings to match your configuration:

```python
# destination data share settings
subscription_id = "<dest_subscription_id>"
account_name = "dest-data-sharexyz"
resource_group_name = "data-share-automation"
subscription_name = "TestSubscription"
dest_file_system_name = "shared-data"
dest_storage_account_name = "deststoragexyz"
```

### Authentication

To automate the acceptance of the invitation sent to the service principal, you must run the `dest.py` script under that identity.

For that, create a `.env` file in the `python` folder and add the following values:

```env
AZURE_CLIENT_ID=client_id
AZURE_CLIENT_SECRET=client_secret
AZURE_TENANT_ID=tenant_id
```

This will ensure the script runs in the context of your service principal account and is able to access the sent invitation.

### Running

Execute the following commands:

```bash
cd python
pip install -r requirements.txt

python source.py
```

After the invitation is accepted, the script can't be run again. If you need to re-run it, please create a new invitation using the `source.py` python script.

After the script executes you should see a subscription setup on the Received Shares on the *destination* azure data share account:

![subscription](./media/subscription_created.png)

You can also see the incoming data being mapped to the *destination* storage account:

![mapping](./media/mapping.png)

Finally, you can see the scheduling setup for the incoming data share:

![trigger](./media/trigger.png)

## Triggering the scan

You can now wait for the scheduled time on the data share subscription or force a snapshot sync in the destination data share account:

![snapshot](./media/snapshot.png)

Soon you will see the Readme.md file in the *destination* storage account, inside the mapped container.

## Additional Work

We can take the destination script and code it as an Azure Function with a timer trigger. This way, we have a reliable way to automate the process of accepting invitations.

Ideally, we want to use the managed identity of the Function App instead of a service principal for this.
That requires the following steps:

- Send the invitation to the Managed Identity of the Function App (the objectId on Azure AD)
- Do not include AZURE_CLIENT_ID, AZURE_CLIENT_SECRET and AZURE_TENANT_ID in the configuration settings of the Function App. This will cause the code to use the managed identity rather than the service principal identity.
- Do some work to handle multiple invitations and configure different mappings.
