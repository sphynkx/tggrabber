This script grabs all messages from Telegram group and generate list of them from defined time range. List transfroms to mediawiki markdown, generated section headers. You have to be in group admins.

* config.ini - Telegram group creds
* favicon.png - icon image for webpage
* README.md - this file
* requirements.txt - necessary modules for Python
* tggrabber.py - grabber script 
* unlock_db - shell cript to unlock sqlite DB (run manually if script freezes)



## Setup

1. Put files into webserver directory or subdirectory

   chmod +x tggrabber.py


2. Configure webserver (this case is nginx, subdir 'mp' in existed domain dir)

```
 location /mp/favicon.png {
        types {} default_type "image/png";
    }

 location /mp/ {
	gzip off;
	root  /var/www/vkapps;
        fastcgi_param SCRIPT_FILENAME $document_root/mp/tggrabber.py;
        fastcgi_buffer_size 10240k;
        fastcgi_buffers 4 10240k;
	fastcgi_pass  unix:/var/run/fcgiwrap.socket;
	include /etc/nginx/fastcgi_params;
    }
```


3. Go to https://my.telegram.org/apps , set new app. Set its params 'api_id' and 'api_hash' to config.ini. From Telegram group settings take group URL and set it to config.ini also.


4. Install necessary Python modules:

   pip install -r requirements.txt


5. At first run the script asks for bot token or mobile number. Enter mobile associated with your Telegram account (bots cannot use some necessary functions of Telegram API). Check message in Telegram service bot with 5-digital code. Enter this code. Now the message would be appear in channel.
Script creates session and json file in current dir.

