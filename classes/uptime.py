# -*- coding: utf-8 -*-


# XEP-0012: Last Activity
class LastActivity:
	""" query the server uptime of the specified domain, defined by XEP-0012 """
	def __init__(self, session, msg, target):
		self.session = session
		self.nick = msg['mucnick']
		self.message_type = msg['type']
		self.target = target

	async def query(self):
		last_activity = await self.session['xep_0012'].get_last_activity(jid=self.target)
		seconds = await last_activity['last_activity']['seconds']

		return seconds

	async def format_values(self, granularity=4):
		seconds = await self.query()
		#seconds = last_activity['last_activity']['seconds']
		uptime = []
		intervals = (
			('years', 31536000),  # 60 * 60 * 24 * 365
			('weeks', 604800),  # 60 * 60 * 24 * 7
			('days', 86400),  # 60 * 60 * 24
			('hours', 3600),  # 60 * 60
			('minutes', 60),
			('seconds', 1)
		)
		for name, count in intervals:
			value = seconds // count
			if value:
				seconds -= value * count
				if value == 1:
					name = name.rstrip('s')
				uptime.append("{} {}".format(value, name))
		result = ' '.join(uptime[:granularity])

		if self.message_type == "groupchat":
			text = "%s: %s is running since %s" % (self.nick, self.target, result)
		else:
			text = "%s is running since %s" % (self.target, result)

		return text
