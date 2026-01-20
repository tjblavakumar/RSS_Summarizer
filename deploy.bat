@echo off
REM RSS Summarizer Deployment Script for Windows
setlocal enabledelayedexpansion

echo === RSS Summarizer Deployment ===

REM Check if terraform is installed
terraform version >nul 2>&1
if errorlevel 1 (
    echo Error: Terraform is not installed. Please install Terraform first.
    exit /b 1
)

REM Check if AWS CLI is configured
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo Error: AWS CLI is not configured. Please run 'aws configure' first.
    exit /b 1
)

REM Generate SSH key pair if it doesn't exist
if not exist "%USERPROFILE%\.ssh\rss_summarizer_key" (
    echo Generating SSH key pair...
    ssh-keygen -t rsa -b 4096 -f "%USERPROFILE%\.ssh\rss_summarizer_key" -N ""
)

REM Create terraform.tfvars
cd terraform
if not exist terraform.tfvars (
    echo Creating terraform.tfvars...
    for /f "delims=" %%i in ('type "%USERPROFILE%\.ssh\rss_summarizer_key.pub"') do set PUBLIC_KEY=%%i
    (
        echo aws_region    = "us-east-1"
        echo project_name  = "rss-summarizer"
        echo instance_type = "t3.small"
        echo public_key    = "!PUBLIC_KEY!"
    ) > terraform.tfvars
)

REM Initialize and apply Terraform
echo Initializing Terraform...
terraform init

echo Planning Terraform deployment...
terraform plan

echo Applying Terraform configuration...
terraform apply -auto-approve

REM Get the public IP
for /f "delims=" %%i in ('terraform output -raw public_ip') do set PUBLIC_IP=%%i
echo Instance deployed at: !PUBLIC_IP!

echo === Deployment Instructions ===
echo 1. Wait 2-3 minutes for the instance to fully initialize
echo 2. Copy your application files to the server:
echo    scp -i %USERPROFILE%\.ssh\rss_summarizer_key -r ../* ec2-user@!PUBLIC_IP!:/home/ec2-user/rss-app/
echo 3. SSH into the server:
echo    ssh -i %USERPROFILE%\.ssh\rss_summarizer_key ec2-user@!PUBLIC_IP!
echo 4. Build and run the Docker container:
echo    cd /home/ec2-user/rss-app
echo    sudo docker-compose up -d
echo 5. Access your application at: http://!PUBLIC_IP!

echo === Deployment Complete ===
pause