# Helpful snippets

## Django service helpful things
- [Setup Django, Nginx, Postgres, Gunicorn](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu)

I have both a gunicorn and a uvicorn server running. gunicorn is for REST calls while the uvicorn is for web sockets.
```
sudo systemctl restart gunicorn
sudo systemctl start gunicorn.socket
sudo systemctl restart uvicorn
sudo systemctl start uvicorn.socket

sudo systemctl status gunicorn
sudo systemctl status uvicorn

sudo vim /etc/nginx/sites-available/poker # config site
sudo vim /etc/systemd/system/gunicorn.service
sudo vim /etc/systemd/system/uvicorn.service

sudo nginx -t
sudo systemctl status nginx
sudo systemctl reload nginx
sudo systemctl restart nginx

sudo tail -f /var/log/supervisor/supervisord.log
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/redis/redis-server.log

sudo journalctl -u uvicorn.service --since "2024-12-19 03:27:38" --follow
```

There was some other guide I had to use to setup Uvicorn for the async (ASGI) stuff. I think I ended up using the Gunicorn guide, but just replaced `gunicorn` with `uvicorn` everywhere.

#### Deploy new Django changes
```
cd ~/django-poker-service/
git pull origin main
rm -rf env/
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
pip install "uvicorn[standard]"
python poker/manage.py migrate
sudo systemctl restart gunicorn
sudo systemctl restart uvicorn
deactivate
```

#### Non-db or env Django changes deploy
```
git pull origin main && sudo systemctl restart gunicorn && sudo systemctl restart uvicorn
```

#### Wipe and restart local dev database
```
rm -f db.sqlite3 && rm -r pokerapp/migrations && python manage.py makemigrations pokerapp && python manage.py migrate
```

## vapor
- [Setup Vapor](https://docs.vapor.codes/deploy/digital-ocean/)
```
sudo vim /etc/supervisor/conf.d/poker.conf # configure
sudo supervisorctl reread # reloads it?
sudo supervisorctl add poker ## ??
sudo supervisorctl update # ?? 
sudo supervisorctl start poker # start vapor poker service
sudo supervisorctl restart poker
curl http://127.0.0.1:8080 # test, should give you an json-formatted not found error
```

#### Deploy new Vapor changes
I'm not sure if this below is quite right.
```
cd ~/vapor-poker-service/
git pull origin main
swift package update
sudo supervisorctl start poker
```

`swiftly install latest` breaks on a 1Gb RAM machine. So I had to upgrade to 2Gb. You can try increasing the swap file size, but I doubt it will work. 
```
sudo mount -o remount,size=2G /tmp
```

## redis
- [Setup Redis](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-22-04)
- [Guide I used for setting up Django Channels](https://channels.readthedocs.io/en/latest/tutorial/part_2.html)

```
sudo nano /etc/redis/redis.conf # config redis
sudo systemctl restart redis.service # restart redis
sudo systemctl status redis # status
redis-cli # command line for redis, try `set test "pee"`; `get test`
```

I did not enable a password for the redis box yet.

On the Digital Ocean guide, it tells you to disable a bunch of commands. That ended up causing a problem for Django channels. I don't know which disabled command caused it, but once I reenabled all the commands in the redis config file, everything worked.

```
redis.exceptions.ResponseError: Unknown Redis command called from script script: 8d28fb4c84249684940e751f9f15170eb9a96e1a, on @user_script:6.
```

## Something about Firebase Push Notiifcations
```
Name:PokerFace
Key ID:4NUY2QJ4VV
Services:Apple Push Notifications service (APNs)
```

## Something about setting up ssh on digital ocean droplet
```
rsync --archive --chown=kasey:kasey ~/.ssh /home/kasey
```