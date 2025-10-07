# Manual Azure Deployment Steps

If you prefer to deploy manually through the Azure Portal, follow these steps:

## 🔐 Option 1: Azure Portal Deployment (Most User-Friendly)

### Step 1: Login to Azure Portal
1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with your Azure account

### Step 2: Create Web App
1. Click **"Create a resource"**
2. Search for **"Web App"** and select it
3. Click **"Create"**

### Step 3: Configure Web App
Fill in the following details:
- **Subscription**: Choose your subscription
- **Resource Group**: Create new → `hostel-gatepass-rg`
- **Name**: `hostel-gatepass-system-[your-unique-id]`
- **Publish**: `Code`
- **Runtime stack**: `Python 3.11`
- **Operating System**: `Linux`
- **Region**: Choose closest to you (e.g., East US)
- **Pricing Plan**: `Basic B1` (or higher)

### Step 4: Review and Create
1. Click **"Review + create"**
2. Click **"Create"**
3. Wait for deployment to complete (2-3 minutes)

### Step 5: Deploy Your Code
1. Go to your Web App resource
2. In the left menu, click **"Deployment Center"**
3. Choose **"GitHub"** as source
4. Authorize GitHub access
5. Select your repository: `HostelGatepassManagementSystem`
6. Select branch: `main`
7. Click **"Save"**

## 🔐 Option 2: Azure CLI Deployment (Fastest)

### Prerequisites
1. Install Azure CLI: `winget install Microsoft.AzureCLI`
2. Restart your terminal

### Quick Deployment Commands
```powershell
# Login to Azure
az login

# Deploy in one command
az webapp up --name hostel-gatepass-system-1234 --resource-group hostel-gatepass-rg --sku B1 --runtime "PYTHON:3.11"
```

## 🔐 Option 3: Use the PowerShell Script

Simply run the provided script:
```powershell
# Run as Administrator
.\deploy_to_azure.ps1
```

## 🔍 After Deployment

### Verify Deployment
1. Visit: `https://your-app-name.azurewebsites.net/health`
2. Should show: "Hostel Gatepass System deployed on Azure ✅"

### Set Up CI/CD (Optional)
1. In Azure Portal → Your Web App → Deployment Center
2. Download **Publish Profile**
3. In GitHub → Settings → Secrets → Actions
4. Add secret: `AZURE_WEBAPP_PUBLISH_PROFILE`
5. Paste the publish profile content

### Configure Environment Variables (Optional)
1. In Azure Portal → Your Web App → Configuration
2. Add Application Settings:
   - `SESSION_SECRET`: Your custom secret key
   - `DATABASE_PATH`: Custom database path (optional)

## 🆘 Troubleshooting

### Common Issues:
1. **App won't start**: Check Application Logs in Azure Portal
2. **Database errors**: Ensure `db_init.py` runs successfully
3. **Import errors**: Verify all dependencies in `requirements.txt`

### Get Logs:
```bash
# View live logs
az webapp log tail --name your-app-name --resource-group hostel-gatepass-rg
```

## 💰 Cost Estimation
- **Basic B1 Plan**: ~$13/month
- **Free F1 Plan**: Available but with limitations
- **Shared D1 Plan**: ~$10/month

Choose the plan that fits your needs and budget.
