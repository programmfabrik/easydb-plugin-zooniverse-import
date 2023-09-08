# coding=utf8

from datetime import datetime
import json
import util


def __parse_row(row, header_ids, logger=None):

    if len(row) < 1:
        return None, None, None, None
    if header_ids == {}:
        return None, None, None, None

    if not 'annotations' in header_ids:
        return None, None, None, None
    if not 'subject_data' in header_ids:
        return None, None, None, None
    if not 'user_name' in header_ids:
        return None, None, None, None
    if not 'created_at' in header_ids:
        return None, None, None, None

    idx_annotations = header_ids['annotations']
    if idx_annotations >= len(row):
        return None, None, None, None
    idx_subject_data = header_ids['subject_data']
    if idx_subject_data >= len(row):
        return None, None, None, None
    idx_user_name = header_ids['user_name']
    if idx_user_name >= len(row):
        return None, None, None, None
    idx_created_at = header_ids['created_at']
    if idx_created_at >= len(row):
        return None, None, None, None

    created_at = None
    try:
        created_at_d = datetime.strptime(row[idx_created_at].strip(), '%Y-%m-%d %H:%M:%S %Z')
        # created_at = created_at_d.strftime('%Y-%m-%dT%H:%M:%S+0:00')
        created_at = created_at_d.strftime('%Y-%m-%d')
    except Exception as e:
        util.warn(str(e), logger)

    try:
        annotations = json.loads(row[idx_annotations].replace('`', '"'))
        subject_data = json.loads(row[idx_subject_data].replace('`', '"'))
        return annotations, subject_data, row[idx_user_name].strip(), created_at
    except Exception as e:
        util.warn(str(e), logger)

    return None, None, None, None


def __parse_subject_data(subject_data) -> str:
    if not isinstance(subject_data, dict):
        return None

    signatur = None

    # first (only?) key has filename info
    for k in subject_data:
        if not 'Filename' in subject_data[k]:
            continue
        filename = subject_data[k]['Filename']
        signatur = filename.split('.')[0]
        if signatur != '':
            return signatur

    return None


def __parse_annotations(annotations) -> dict:
    if not isinstance(annotations, list):
        return None

    parsed_annotations = {}
    for a in annotations:
        if not 'task' in a:
            continue
        if not 'value' in a:
            continue

        question = a['task']
        if question in parsed_annotations:
            continue

        answer = a['value']

        if isinstance(answer, str):
            answer = answer.strip()
            if answer == '':
                continue
            parsed_annotations[question] = answer
            continue

        if isinstance(answer, list):
            answers = []

            for v in answer:
                if not 'answers' in v:
                    continue
                if not isinstance(v['answers'], dict):
                    continue

                for k in v['answers']:
                    if not isinstance(v['answers'][k], list):
                        continue

                    answers += v['answers'][k]

            if len(answers) > 0:
                parsed_annotations[question] = answers
                continue

    if parsed_annotations == {}:
        return None

    return parsed_annotations


def parse_data(data, logger=None) -> dict:
    if data is None:
        raise Exception('no valid zooniverse csv data!')

    csv_data = util.get_json_value(json.loads(data), 'csv')
    if not isinstance(csv_data, list):
        raise Exception('no valid zooniverse csv data!')

    first = True
    header_ids = {}

    collected_objects = {}
    valid_rows = 0
    empty_annotation_rows = 0

    for row in csv_data:
        if len(row) < 1:
            continue

        if first:
            first = False
            for i in range(len(row)):
                header_ids[row[i]] = i
            continue

        annotations, subject_data, user_name, created_at = __parse_row(row, header_ids, logger)
        if annotations is None:
            continue
        if subject_data is None:
            continue
        if user_name is None or user_name == '':
            user_name = '<unknown>'
        if created_at is None or created_at == '':
            created_at = None

        # parse signatur from subject_data
        signatur = __parse_subject_data(subject_data)
        if signatur is None:
            continue

        valid_rows += 1

        # parse answers from annotations
        answers = __parse_annotations(annotations)
        if answers is None:
            empty_annotation_rows += 1
            continue

        if not signatur in collected_objects:
            collected_objects[signatur] = {}
        if not user_name in collected_objects[signatur]:
            collected_objects[signatur][user_name] = {}
        collected_objects[signatur][user_name][created_at] = answers

    util.info('parsed {0} objects from {1} csv rows. skipped {2} rows with empty annotations'.format(
        len(collected_objects), valid_rows, empty_annotation_rows), logger)

    return collected_objects, {
        'count': {
            'parsed_rows': valid_rows,
            'parsed_objs': len(collected_objects),
        }
    }
