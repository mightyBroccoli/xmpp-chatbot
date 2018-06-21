# Python XMPP Chatbot

## beforehand
Do not opperate this bot on foreign servers.

### functions
- query xmpp server software and version [XEP-0092](https://xmpp.org/extensions/xep-0092.html)
- query xmpp server uptime [XEP-0012](https://xmpp.org/extensions/xep-0012.html)
- displaying a help output
- respond to username being mentioned

### todo
- [ ] query xmpp server contact addresses [XEP-0157](https://xmpp.org/extensions/xep-0157.html)
  - [x] iq is being catched but the answer needs to be extracted out of it
- [ ] Github Webhook

### install
#### requirements
- slixmpp
- configparser
- datetime
- random

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
 If done correctly `./main.py &` and enjoy your bot.