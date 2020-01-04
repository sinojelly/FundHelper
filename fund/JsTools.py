# -*- coding: utf-8 -*-

from execjs._exceptions import ProcessExitedWithNonZeroStatus


def eval_js(js_content, key, default=''):
    try:
        result = js_content.eval(key)
    except ProcessExitedWithNonZeroStatus as err:
        import logging
        _logger = logging.getLogger('werkzeug')
        _logger.info("eval js exceptiono, key = " + key + ", exception: " + str(err))
        result = default
    return result
