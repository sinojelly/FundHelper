# -*- coding: utf-8 -*-

import requests

import logging
_logger = logging.getLogger('werkzeug')


def request_url(url, module):
	try:
		# 用requests获取到对应的文件
		content = requests.get(url)
	except NewConnectionError as err:
		_logger.error(module + " request url fail: " + url + " NewConnectionError: " + str(err))
		return None

	if content.status_code != 200:
		print(module + " fetch info failed (" + content.status_code + ")")
		return None
	
	return content
