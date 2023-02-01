# coding=utf8

import json
import sys
import traceback


def handle_exceptions(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exc_info = sys.exc_info()
            stack = traceback.extract_stack()
            tb = traceback.extract_tb(exc_info[2])
            full_tb = stack[:-1] + tb
            exc_line = traceback.format_exception_only(*exc_info[:2])

            trace = [str(repr(e))] + traceback.format_list(full_tb) + exc_line

            print('\n'.join(trace))

    return func_wrapper


def dumpjs(js, indent=4):
    return json.dumps(js, indent=indent)


def json_response(js, statuscode=200):
    return {
        'status_code': statuscode,
        'body': dumpjs(js),
        'headers': {
            'Content-Type': 'application/json; charset=utf-8'
        }
    }


def json_error_response(msg):
    return json_response(
        {
            'error': msg
        },
        statuscode=400
    )
