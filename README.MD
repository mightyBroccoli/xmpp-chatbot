# Python XMPP Chatbot

## beforehand
Do not opperate this bot on foreign servers.

### functions
- query xmpp server software and version [XEP-0092](https://xmpp.org/extensions/xep-0092.html)
- query xmpp server uptime [XEP-0012](https://xmpp.org/extensions/xep-0012.html)
- query xmpp server contact addresses [XEP-0157](https://xmpp.org/extensions/xep-0157.html)
- display help output
- respond to username being mentioned

### todo
- [ ] Github Webhook

### install
#### requirements
- slixmpp
- configparser
- datetime
- random
- validators

#### configuration
`bot.cfg` replace dummy file with correct credentials/ parameters
````cfg
[Account]
jid=nick@domain.tld/querybot-0.1
password=super_secret_password
[MUC]
rooms=room_to_connect_to@conference.domain.tld
nick=mucnickname
[ADMIN]
admins=admins ( ! muc nick and not the jid nickname)
````

##### systemd
Copy the systemd dummy file into systemd service folder.
`systemdctl daemon-reload` and `systemctl start magicbot.service` to start the bot.
If it is neccecary to start the bot automatically when the system boots do `systemctl enable magicbot.service`.

#### starting the bot without systemd
Got to the bots directory and run `./main.py &`.