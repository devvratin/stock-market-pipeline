# Provision Azure Data Lake Storage Gen2 (ADLS Gen2) for Nifty 50 Stress Monitor
# Prerequisite: run `az login` first.

param(
    [string]$ResourceGroup = "rg-nifty-stress",
    [string]$Location = "centralindia",
    [string]$StorageAccount = "stniiftystress$(Get-Random -Maximum 9999)",
    [string]$ContainerName = "market-stress"
)

az group create --name $ResourceGroup --location $Location

# --hns true enables Hierarchical Namespace (this makes it ADLS Gen2)
az storage account create `
    --name $StorageAccount `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Standard_LRS `
    --kind StorageV2 `
    --hns true

az storage container create `
    --name $ContainerName `
    --account-name $StorageAccount `
    --auth-mode login

Write-Host "`nADLS Gen2 ready! Fetch your connection string with:"
Write-Host "az storage account show-connection-string -g $ResourceGroup -n $StorageAccount -o tsv"