# setting up EC2 servers to run measurements

## Launching instance
Launch instance normally, only special thing is in Network settings, select launch-wizard-3.

Alternatively, set Inbound rules on the Instances page to the following:
```
22	TCP	0.0.0.0/0	
5000	TCP	0.0.0.0/0	(assuming auth server running on port 5000)
80	TCP	0.0.0.0/0	
443	TCP	0.0.0.0/0
```
This allows inbound http and https traffic

## setting up gunicorn and nginx
Click on Connect -> SSH Client -> SSH into EC2

pip install all the required packages, and check if app is working locally

`sudo apt-get install nginx` to install nginx

to test if working: `sudo systemctl start nginx` and `sudo systemctl enable nginx`

Find the public IPv4 address of server from the Connect page of EC2, go to it using browser, see if nginx page show up

Open the file `/etc/nginx/sites-available/default` with something like `sudo vim /etc/nginx/sites-available/default` 

Edit location to be
```
large_client_header_buffers 4 64k;
location / {
  proxy_pass http://127.0.0.1:5000;
  client_max_body_size 0;
}
```

run `sudo systemctl restart nginx`

`sudo apt-get install gunicorn` to install gunicorn

`gunicorn -b 0.0.0.0:5000 app:app` to start the app

Go to the public IP address and see if its working!

