#!/usr/bin/python3
##  Based on https://proglib.io/p/pishem-prostoy-grabber-dlya-telegram-chatov-na-python-2019-11-06
## Grab group messages and comment, generate list of them with mediawiki markup

import configparser, cgi
import json, datetime, locale
from datetime import date, datetime

## Work with Telegram API
from telethon.sync import TelegramClient
from telethon import connection
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
## Get user info
from telethon import functions, types
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
## Work with messages
from telethon.tl.functions.messages import GetHistoryRequest


## Correct date cyrillization
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
rumonth = ['нулября', 'января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября','декабря']

## Get Telegram creds
config = configparser.ConfigParser()
config.read("config.ini")
api_id   = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
username = config['Telegram']['username']
url      = config['TGGroup']['group']

client = TelegramClient(username, api_id, api_hash)

client.start()

## Start: Block for download all group contents
## dump_all_participants() not used because it doesnt consider unregistered users
async def dump_all_participants(channel):
    '''Write info about all participants to separate json-file'''
    offset_user = 0    ## user number to begin
    limit_user = 100   ## max amount of users for one iteration

    all_participants = []   ## list of all participants
    filter_user = ChannelParticipantsSearch('')

    while True:
        participants = await client(GetParticipantsRequest(channel,
            filter_user, offset_user, limit_user, hash=0))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset_user += len(participants.users)

    all_users_details = []   ## list of dicts with necessary params

    for participant in all_participants:
        all_users_details.append({"id": participant.id,
            "first_name": participant.first_name,
            "last_name": participant.last_name,
            "user": participant.username,
            "phone": participant.phone,
            "is_bot": participant.bot})

    with open('channel_users.json', 'w', encoding='utf8') as outfile:
        json.dump(all_users_details, outfile, ensure_ascii=False)


async def dump_all_messages(channel):
    '''Write info about all msgs to separate json-file'''
    offset_msg = 0    ## msg number to begin
    limit_msg = 100   ## max amount of users for one iteration

    all_messages = []   ## list of all msgs
    total_messages = 0
    total_count_limit = 0  ## modify it if you need not all msgs

    class DateTimeEncoder(json.JSONEncoder):
        '''Class for serialization of date params in JSON'''
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            if isinstance(o, bytes):
                return list(o)
            return json.JSONEncoder.default(self, o)

    while True:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=offset_msg,
            offset_date=None, add_offset=0,
            limit=limit_msg, max_id=0, min_id=0,
            hash=0))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            all_messages.append(message.to_dict())
        offset_msg = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break

    with open('channel_messages.json', 'w', encoding='utf8') as outfile:
         json.dump(all_messages, outfile, ensure_ascii=False, cls=DateTimeEncoder)
## End: Block for download all group contents


## Get user info (modified version). Returns in wiki-format already
def getname(id):
        my_user    = client.get_entity( PeerUser( int(id) ))
        fn = my_user.first_name if my_user.first_name else ""
        ln = my_user.last_name if my_user.last_name else ""
        return '<b>© ' + fn + ' ' + ln + '</b>'


## Get msgs and format them
def wikitext(data, yset = 0, mset = 0, dset = 0):
    wikitext = []
    yhead, mhead, dhead = 0, 0, 0 ## these valuse for control in wiki-headers generation
    for d in data:
        if(d['_'] == 'Message'):
            dateserial = datetime.strptime(d['date'], '%Y-%m-%dT%H:%M:%S%z')
            if(yset == dateserial.year and mset == dateserial.month and dset == dateserial.day): break ## cut ancient history (in order to date from form)
            if(int(dateserial.year) != yhead):
                wikitext.append("\n\n= " + str(dateserial.year) + " =\n") ## add header only for first entry of year
                yhead = dateserial.year
            if(dateserial.month != mhead):
                wikitext.append("\n== " + dateserial.strftime("%OB") + " ==\n") ## add header only for first entry of month
                mhead = dateserial.month
            if(dateserial.day != dhead):
                wikitext.append("\n=== " + str(dateserial.day) + ' ' + rumonth[int(dateserial.strftime("%m"))] + " ===\n") ## add header only for first entry of day
                dhead = dateserial.day
            uid = 'GroupAdmin'
            try:
                uid = getname(d['from_id']['user_id'])
            except:
                uid = 'GroupAdmin'
            wikitext.append('<hr width="20%"><p><pre>{}</pre><br>\n{}<br>\n[https://t.me/c/{}/{} {}]<br>\n</p>'.format(d['message'], uid, d['peer_id']['channel_id'], d['id'], dateserial.strftime("%Y-%m-%d %H:%M:%S")))
        print('\n'.join(wikitext))
        wikitext.clear()



async def main():
    channel = await client.get_entity(url)
    await dump_all_participants(channel)
    await dump_all_messages(channel)


with client:
    client.loop.run_until_complete(main())
    data = json.load(open("channel_messages.json", "rb"))
    print('Content-Type: text/html')
    print('')
    ## You may modify 'min' and 'max' params in input tag to range dates in calendar
    print('''
<html>
<head>
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" href="favicon.png" />
<title>Telegram Grabber (MicroPoezium)</title>
</head>
<body>
<h2>Telegram Grabber (MicroPoezium)</h2>
<form name="search" action="" method="post">
Choose the some recent date: <br><br>
<input type="date" name="datebox"  min="2024-01-25" max="{}"><br><br>
or simply push button for full output:<br><br>
<input type="submit" name="buttonname" value="Get Wiki-text">
</form>'''.format(date.today()))

    form = cgi.FieldStorage()
    datebox =  form.getvalue('datebox') or "2024-01-25"
    buttname =  form.getvalue('buttonname') or "NON"
#### fix because list is from next day after entered date
    from datetime import timedelta
    date = datetime.strptime(datebox, '%Y-%m-%d') - timedelta(1)

## Wait while user enter date or simply push button
## Strange but script works. Although time.sleep gets error to log:  name 'time' is not defined" But if add import time
## script freezes on load. Also if sleep comment out (with or without import time).
    while(buttname == "NON"): 
        buttname =  form.getvalue('buttonname') or "NON"
        time.sleep(1)

    print('<hr><br><textarea  rows="25" cols="100">')
    data = json.load(open("channel_messages.json", "rb"))
    wikitext(data, date.year, date.month, date.day)
    print("</textarea>")
    print('''
<p><br><button>Выделить и скопировать вики-текст</button></p><br>
<hr width=50% align=left><font color=silver>Written by <a href='https://t.me/sphynkx' style='color:silver'>Sphynkx</a> © 2024</font>
<script>
document.querySelector("button").onclick = function(){
    document.querySelector("textarea").select();
    document.execCommand('copy');
}
</script>
</body></html>
    ''')

