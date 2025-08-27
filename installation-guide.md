a comprehensive step-by-step guide to set up a Frappe development and deployment environment locally on Windows.I'll provide you with a comprehensive step-by-step guide to set up Frappe Framework development and deployment environment locally on Windows. Based on the latest information, here are three recommended approaches:

Method 1: WSL2 + Ubuntu (Recommended for Development)
This is the officially recommended approach for Windows users as Frappe Framework requires a Unix-like environment.

Step 1: Enable WSL2 on Windows
PowerShell
# Run PowerShell as Administrator
# Enable WSL feature
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart your computer
After restart:

PowerShell
# Set WSL2 as default version
wsl --set-default-version 2

# Install Ubuntu 22.04 LTS
wsl --install -d Ubuntu-22.04
Step 2: Configure WSL2 Performance (Optional but Recommended)
Create .wslconfig file in your Windows user directory (%UserProfile%):

INI
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
Step 3: Set Up Ubuntu Environment
Launch Ubuntu from Start Menu and run:

bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential dependencies
sudo apt install -y \
    git python3-dev python3-pip python3-testresources \
    software-properties-common mariadb-server \
    redis-server xvfb libfontconfig curl \
    build-essential libssl-dev libffi-dev \
    python3-venv python3-setuptools

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Yarn
npm install -g yarn

# Install wkhtmltopdf
sudo apt install -y wkhtmltopdf
Step 4: Configure MariaDB
bash
# Secure MariaDB installation
sudo mysql_secure_installation

# Configure MariaDB for Frappe
sudo mysql -u root -p
In MySQL prompt:

SQL
-- Create database user for Frappe
CREATE USER 'frappe'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON *.* TO 'frappe'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EXIT;
Edit MariaDB configuration:

bash
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
Add these settings under [mysqld]:

INI
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
Restart MariaDB:

bash
sudo service mysql restart
Step 5: Install Frappe Bench
bash
# Install bench using pip
pip3 install frappe-bench

# Add local bin to PATH
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Verify installation
bench --version
Step 6: Create Your First Frappe Site
bash
# Create a new bench directory
bench init frappe-bench --frappe-branch version-15
cd frappe-bench

# Create a new site
bench new-site mysite.local --db-root-password your_mysql_root_password

# Set the site as default
bench use mysite.local

# Start the development server
bench start
Step 7: Access Your Site
Open your Windows browser and navigate to:

http://localhost:8000 - Your Frappe site
http://localhost:8001 - Frappe desk (admin interface)
Default login credentials:

Username: Administrator
Password: (password you set during site creation)
Method 2: Docker Development Environment
For a more isolated development environment:

Step 1: Install Docker Desktop for Windows
Download and install Docker Desktop from the official website.

Step 2: Clone Frappe Docker
bash
# In WSL2 or Git Bash
git clone https://github.com/frappe/frappe_docker.git
cd frappe_docker
Step 3: Start Development Environment
bash
# Copy example environment file
cp example.env .env

# Start development containers
docker compose -f compose.yaml \
    -f overrides/compose.redis.yaml \
    -f overrides/compose.mariadb.yaml \
    -f overrides/compose.noproxy.yaml \
    up -d

# Create a site
docker compose exec backend bench new-site mysite.local --no-mariadb-socket
Step 4: Access the Site
Navigate to http://localhost:8080 in your browser.

Method 3: VirtualBox + Ubuntu Server
For those who prefer a full VM approach:

Step 1: Install VirtualBox
Download and install VirtualBox from Oracle's website.

Step 2: Create Ubuntu VM
Download Ubuntu Server 22.04 LTS ISO
Create new VM with:
RAM: 4GB minimum (8GB recommended)
Storage: 50GB minimum
Network: NAT with port forwarding
Step 3: Configure Port Forwarding
In VirtualBox VM settings:

Host Port 8000 → Guest Port 8000 (Frappe site)
Host Port 8001 → Guest Port 8001 (Desk)
Host Port 22 → Guest Port 22 (SSH)
Step 4: Install Frappe
Follow the same Ubuntu installation steps from Method 1 inside your VM.

Development Workflow
Creating a Custom App
bash
# Create new app
cd frappe-bench
bench new-app my_custom_app

# Install app to site
bench --site mysite.local install-app my_custom_app

# Start development
bench start
Development Commands
bash
# Migrate database after changes
bench --site mysite.local migrate

# Clear cache
bench --site mysite.local clear-cache

# Restart bench
bench restart

# Update apps
bench update

# Backup site
bench --site mysite.local backup

# Restore backup
bench --site mysite.local restore path/to/backup.sql.gz
IDE Setup
For the best development experience:

VS Code with WSL Extension:

Install "Remote - WSL" extension
Open WSL folder directly in VS Code
Install Python and Frappe extensions
Configure Python Path:

JSON
{
    "python.defaultInterpreterPath": "./env/bin/python",
    "python.linting.enabled": true
}
Production Deployment Preparation
Using Frappe Cloud (Easiest)
Sign up for Frappe Cloud
Deploy your custom app from GitHub repository
Configure domain and SSL automatically
Self-Hosted Production
bash
# Install production dependencies
sudo apt install supervisor nginx

# Configure production site
bench setup production [frappe-user]

# Enable site for production
bench --site mysite.local enable-scheduler
bench --site mysite.local set-maintenance-mode off
Troubleshooting Common Issues
Port Already in Use
bash
# Kill processes on specific ports
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:8001 | xargs kill -9
Permission Issues
bash
# Fix ownership
sudo chown -R $USER:$USER frappe-bench/
MariaDB Connection Issues
bash
# Restart MariaDB
sudo service mysql restart

# Check status
sudo service mysql status
Memory Issues in WSL2
Add to .wslconfig:

INI
[wsl2]
memory=8GB
swap=2GB
This setup gives you a complete Frappe development environment on Windows that closely mirrors production environments while providing excellent development tools and workflows.
