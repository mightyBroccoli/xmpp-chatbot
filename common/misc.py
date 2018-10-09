# -*- coding: utf-8 -*-
import validators
from common.strings import StaticAnswers


def deduplicate(reply):
	"""
	list deduplication method
	:param list reply: list containing non unique items
	:return: list containing unique items
	"""
	reply_dedup = list()
	for item in reply:
		if item not in reply_dedup:
			reply_dedup.append(item)

	return reply_dedup


def validate(wordlist, index):
	"""
	validation method to reduce malformed querys and unnecessary connection attempts
	:param wordlist: words separated by " " from the message
	:param index: keyword index inside the message
	:return: true if valid
	"""
	# keyword inside the message
	argument = wordlist[index]

	# check if argument is in the argument list
	if argument in StaticAnswers().keys(arg='list'):
		# if argument uses a domain check for occurrence in list and check domain
		if argument in StaticAnswers().keys(arg='list', keyword='domain_keywords'):
			try:
				target = wordlist[index + 1]
				if validators.domain(target):
					return True
				elif validators.email(target):
					return True

			except IndexError:
				# except an IndexError if a keywords is the last word in the message
				return False

		# check if number keyword is used if true check if target is assignable
		elif argument in StaticAnswers().keys(arg='list', keyword='number_keywords'):
			try:
				if wordlist[index + 1]:
					return True
			except IndexError:
				# except an IndexError if target is not assignable
				return False
		# check if argument is inside no_arg list
		elif argument in StaticAnswers().keys(arg='list', keyword="no_arg_keywords"):
			return True
		else:
			return False
	else:
		return False
