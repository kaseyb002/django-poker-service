# Helpful snippets

## Guides I used
- [Setup Redis](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-22-04)
- [Setup Django, Nginx, Postgres, Gunicorn](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu)
- [Setup Vapor](https://docs.vapor.codes/deploy/digital-ocean/)

There was some other guide I had to use to setup Vunicorn for the async (ASGI) stuff. I think I ended up using the Gunicorn guide, but just replaced `gunicorn` with `vunicorn` everywhere.

## Django service helpful things
```
sudo systemctl restart gunicorn
sudo systemctl start gunicorn.socket

sudo systemctl status gunicorn

sudo systemctl status nginx
sudo systemctl restart nginx
```

#### Wipe and restart database
```
rm -f db.sqlite3 && rm -r pokerapp/migrations && python manage.py makemigrations pokerapp && python manage.py migrate
```

## vapor
```
sudo vim /etc/supervisor/conf.d/poker.conf # configure
sudo supervisorctl reread # reloads it?
sudo supervisorctl add poker ## ??
sudo supervisorctl update # ?? 
sudo supervisorctl start poker # start vapor poker service
curl http://127.0.0.1:8080 # test
```

`swiftly install latest` breaks on a 1Gb RAM machine. So I had to upgrade to 2Gb. You can try increasing the swap file size, but I doubt it will work. 
```
sudo mount -o remount,size=2G /tmp
```

## redis
`sudo systemctl restart redis.service`

`swiftly install latest` can freeze up your machine. You'll need to turn off the Droplet via the digital ocean toggle GUI. 

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
