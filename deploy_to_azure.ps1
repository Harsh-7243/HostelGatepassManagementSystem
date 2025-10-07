# Azure Deployment Script for Hostel Gatepass Management System
# Run this script in PowerShell as Administrator

Write-Host "🚀 Azure Deployment Script for Hostel Gatepass Management System" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green

# Check if Azure CLI is installed
try {
    $azVersion = az --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Azure CLI is installed" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Azure CLI not found. Installing..." -ForegroundColor Yellow
    Write-Host "Please install Azure CLI first:" -ForegroundColor Yellow
    Write-Host "winget install Microsoft.AzureCLI" -ForegroundColor Cyan
    Write-Host "Or download from: https://aka.ms/installazurecliwindows" -ForegroundColor Cyan
    exit 1
}

# Login to Azure
Write-Host "`n🔐 Step 1: Login to Azure" -ForegroundColor Blue
Write-Host "This will open a browser window for secure authentication..." -ForegroundColor Yellow
az login

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Azure login failed. Please try again." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Successfully logged in to Azure" -ForegroundColor Green

# Set variables
$APP_NAME = "hostel-gatepass-system-$(Get-Random -Minimum 1000 -Maximum 9999)"
$RESOURCE_GROUP = "hostel-gatepass-rg"
$LOCATION = "East US"
$RUNTIME = "PYTHON:3.11"
$SKU = "B1"

Write-Host "`n📝 Deployment Configuration:" -ForegroundColor Blue
Write-Host "App Name: $APP_NAME" -ForegroundColor Cyan
Write-Host "Resource Group: $RESOURCE_GROUP" -ForegroundColor Cyan
Write-Host "Location: $LOCATION" -ForegroundColor Cyan
Write-Host "Runtime: $RUNTIME" -ForegroundColor Cyan
Write-Host "SKU: $SKU" -ForegroundColor Cyan

# Create resource group
Write-Host "`n🏗️  Step 2: Creating Resource Group" -ForegroundColor Blue
az group create --name $RESOURCE_GROUP --location $LOCATION

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create resource group" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Resource group created successfully" -ForegroundColor Green

# Deploy the web app
Write-Host "`n🚀 Step 3: Deploying Web App" -ForegroundColor Blue
Write-Host "This may take a few minutes..." -ForegroundColor Yellow

az webapp up --name $APP_NAME --resource-group $RESOURCE_GROUP --location $LOCATION --runtime $RUNTIME --sku $SKU

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host "`n🎉 Deployment Successful!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "Your app is now live at: https://$APP_NAME.azurewebsites.net" -ForegroundColor Cyan
Write-Host "Health check: https://$APP_NAME.azurewebsites.net/health" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Test your application at the URL above" -ForegroundColor White
Write-Host "2. Set up custom domain (optional)" -ForegroundColor White
Write-Host "3. Configure SSL certificate (optional)" -ForegroundColor White
Write-Host "4. Set up monitoring and alerts" -ForegroundColor White
Write-Host "`nResource Group: $RESOURCE_GROUP" -ForegroundColor Cyan
Write-Host "Manage your app at: https://portal.azure.com" -ForegroundColor Cyan
