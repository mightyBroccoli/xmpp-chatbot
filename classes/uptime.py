# -*- coding: utf-8 -*-


# XEP-0012: Last Activity
class LastActivity:
	"""
	query the server uptime of the specified domain, defined by XEP-0012
	"""
	def __init__(self):
		# init all necessary variables
		self.last_activity = None
		self.target, self.opt_arg = None, None

	def process(self, granularity=4):
		seconds = self.last_activity['last_activity']['seconds']
		uptime = []

		# touple with displayable time sections
		intervals = (
			('years', 31536000),  # 60 * 60 * 24 * 365
			('weeks', 604800),  # 60 * 60 * 24 * 7
			('days', 86400),  # 60 * 60 * 24
			('hours', 3600),  # 60 * 60
			('minutes', 60),
			('seconds', 1)
		)

		# for every element in possible time section process the seconds
		for name, count in intervals:
			value = seconds // count
			if value:
				seconds -= value * count
				if value == 1:
					name = name.rstrip('s')
				uptime.append("{} {}".format(value, name))
		result = ' '.join(uptime[:granularity])

		# insert values into result string
		text = "%s is running since %s" % (self.target, result)

		return text

	def format(self, query, target, opt_arg):
		self.last_activity = query

		self.target = target
		self.opt_arg = opt_arg

		reply = self.process()
		return reply
