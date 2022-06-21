# LeykaDonationsPublisher
The Bot publishes donations in Telegram's groups or channels, that users have sent by 
WordPress's plugin the Leyka.


## How does the Bot work?  
- You can add the Bot in your group or super group
- You can add the Bot in a channel and make it administrator with privileges to send messages. 
Then you have to write message to the Bot: `/run @channel`, where `channel` - it is a channel's ID. 
You can find it in the channel's settings in the Bot's link: `https://t.me/channel`. 
Before this the Bot is going to publish information about donations from your WordPress site.
- The Bot sends messages in channels or groups if somebody donate money by the Leyka plugin. 
Message looks like: 
    ```
    Hi! It is a header. Change me plz.
    Як Яков пожертовал 100 rub
    ...
    There is a footer. Change me plz.
    ```
    Then you can change header and footer by commands `/header` and `/footer` _if you are the Bot's
    administrator_.

### Usage
`/run @channelName` - add your channel to the Bot's mailing list; _the Bot must be in chanel's administrators list_.  
`/header your header's text` - change header's text to `your header's text`  
`/footer your footer's text` - change footer's text to `your footer's text`  


## Requirements
* Python >= 3.7 with requirements:
    - PyYaml==6.0
    - python-telegram-bot==13.12
    - mysql-connector-python==8.0.29
    
    
## Install

### Create python's virtual environment
_You need Python >= 3.7._   
You have to run command `python3 -m venv ./.venv` in work directory for create virtual environment.  
Then install requirements:
```
.venv/bin/python3 -m pip install PyYaml==6.0
.venv/bin/python3 -m pip install python-telegram-bot==13.12
.venv/bin/python3 -m pip install mysql-connector-python==8.0.29
```
Check that your requirements have been installed successfully: `.venv/bin/python3 -m pip list`.  
You should see something like this (__your requirements may be different versions__):
```
Package                Version                                                                                                 
---------------------- -----------                                                                                             
APScheduler            3.6.3                                                                                                   
backports.zoneinfo     0.2.1                                                                                                   
cachetools             4.2.2                                                                                                   
certifi                2022.5.18.1                                                                                             
mysql-connector-python 8.0.29                                                                                                  
pip                    20.2.4                                                                                                  
protobuf               4.21.1                                                                                                  
python-telegram-bot    13.12                                                                                                   
pytz                   2022.1                                                                                                  
pytz-deprecation-shim  0.1.0.post0                                                                                             
PyYAML                 6.0                                                                                                     
setuptools             58.3.0                                                                                                  
six                    1.16.0                                                                                                  
tornado                6.1                                                                                                     
tzdata                 2022.1                                                                                                  
tzlocal                4.2  
```


## Starting  

### Configuration
Before starting the Bot you have to specify the Bot's configuration:  
```
bot:
  name: yourBotUsernameWithout@
  token: yourBotToken
  admin_id: BotAdministatorID  # this user can execute /footer and /header commands.
database:
  donations:  # WordPress' DB
    user: yourDBUsername
    password: yourDBPassword
    host: yourDBHostname
    database: yourDBName
    raise_on_warnings: True
  data:  # SQLite DB
    db_name: bot_data.db
```

### Start the Bot
The Bot starts via `main.py` file.  
You can use the Bot two ways:
- configuring cron to execute:  
`*/15 * * * * python donation_publisher_bot/main.py`  
where `python` it is a path to python's virtual environment.
- run the Bot in loop via command line args `loop` and `sleep`:  
`python python donation_publisher_bot/main.py --loop --sleep 15`  

