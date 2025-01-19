#!/bin/bash
sudo apt update;
sudo apt upgrade -y;

# python
sudo apt install python3 python3-dev -y;
sudo apt install lib2to3;
# postgresql
# sudo apt install postgresql postgresql-contrib libpq-dev -y
# sudo apt install postgis postgresql-16-postgis-3

# libgdal
# sudo apt-get install libgdal-dev -y;
# sudo apt-get install libq-dev -y;

# redis
sudo apt-get install lsb-release curl gpg;
curl -fsSL https://packages.redis.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg;
sudo chmod 644 /usr/share/keyrings/redis-archive-keyring.gpg;
echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/redis.list;
sudo apt-get update;
sudo apt-get install redis -y;
sudo systemctl enable redis-server;
sudo systemctl start redis-server;

# other dependencies
sudo apt install git -y;


#nginx
sudo apt install nginx -y
sudo cp dev.motaa.net.conf /etc/nginx/sites-available/
sudo systemctl restart nginx
sudo ln -s /etc/nginx/sites-available/dev.motaa.net.conf /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# gunicorn
sudo cp gunicorn.service /etc/systemd/system/
sudo cp gunicorn.socket /etc/systemd/system/
sudo systemctl daemon-reload
systemctl enable nginx.service
systemctl enable --now gunicorn.socket

# app setup
DIR="motaa_backend"

if [ -d "$DIR" ]; then
  echo "Directory $DIR exists. Deleting..."
  rm -rf "$DIR"
else
  echo "Directory $DIR does not exist."
fi
git clone --single-branch --branch staged git@github.com:MilliHub-dev/motaa_backend.git;
cd motaa_backend;
python3 -m venv venv;
source venv/bin/activate;
# cp ../.env .env;
pip install -r requirements;
python manage.py collectstatic; # remove when using cloud storage
python manage.py runserver;

