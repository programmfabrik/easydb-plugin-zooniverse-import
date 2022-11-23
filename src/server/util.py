# coding=utf8

import json


def json_response(js, statuscode=200):
    return {
        'status_code': statuscode,
        'body': json.dumps(js, indent=4),
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
