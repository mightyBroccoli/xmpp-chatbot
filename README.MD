# Python XMPP Chatbot

## beforehand
Do not operate this bot on foreign servers. Many servers prohibit the usage of bots on their service.

### functions
- query xmpp server software and version [XEP-0092](https://xmpp.org/extensions/xep-0092.html)
- query xmpp server uptime [XEP-0012](https://xmpp.org/extensions/xep-0012.html)
- query xmpp server contact addresses [XEP-0157](https://xmpp.org/extensions/xep-0157.html)
- display information about XEP from the [XSF extensions website](https://xmpp.org/extensions/)
- display help output
- respond to username being mentioned

### install
#### virtualenv
With virtualenv it is possible to run the bot inside a virtual environment without disrupting other python processes
 and or dependencies. This repo comes with a `requirements.txt` to make the install process as easy as possible.
 ````bash
cd to_the_path/of_the_bot/
mkdir ./venv

# create the virtual environment
virtualenv -p $(which python3) ./venv
source ./venv/bin/activate
pip3 install -r requirements.txt
````

#### configuration
Replace the dummy `bot.cfg` file, filled with correct credentials/ parameters.
````cfg
[Account]
jid=nick@domain.tld/querybot
password=super_secret_password
[MUC]
rooms=room_to_connect_to@conference.domain.tld,another_room@conference.domain.tld
nick=mucnickname
````

##### systemd
Copy the systemd dummy file into systemd service folder.
`systemdctl daemon-reload` and `systemctl start magicbot.service` to start the bot.
If it is neccecary to start the bot automatically when the system boots do `systemctl enable magicbot.service`.

#### starting the bot without systemd
Got to the bots directory and run `./main.py &`.