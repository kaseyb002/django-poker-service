# Helpful snippets

## Django service helpful things
- [Setup Django, Nginx, Postgres, Gunicorn](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu)
```
sudo systemctl restart gunicorn
sudo systemctl start gunicorn.socket

sudo systemctl status gunicorn

sudo vim /etc/nginx/sites-available/poker # config site

sudo nginx -t
sudo systemctl status nginx
sudo systemctl reload nginx
sudo systemctl restart nginx
```

There was some other guide I had to use to setup Vunicorn for the async (ASGI) stuff. I think I ended up using the Gunicorn guide, but just replaced `gunicorn` with `vunicorn` 
everywhere.

#### Deploy new Django changes
```
cd ~/django-poker-service/
git pull origin main
source env/bin/activate
python poker/manage.py migrate
sudo systemctl restart gunicorn
quit
```

#### Wipe and restart database
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
```
cd ~/vapor-poker-service/
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