# -*- coding: utf-8 -*-

from execjs._exceptions import ProcessExitedWithNonZeroStatus, ProgramError


def eval_js(js_content, key, default=''):
    import logging
    _logger = logging.getLogger('werkzeug')

    try:
        result = js_content.eval(key)
    except ProcessExitedWithNonZeroStatus as err:
        _logger.info("eval js got ProcessExitedWithNonZeroStatus, key = " + key + ", exception: " + str(err))
        result = default
    except ProgramError as perr:
        _logger.info("eval js got ProgramError, key = " + key + ", exception: " + str(perr))
        result = default

    return result
