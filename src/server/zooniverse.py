# coding=utf8

from datetime import datetime
import json
import csv


def parse_csv_row(row, header_ids, logger):

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
        created_at_d = datetime.strptime(
            row[idx_created_at].strip(),
            '%Y-%m-%d %H:%M:%S %Z'
        )
        created_at = created_at_d.strftime('%Y-%m-%dT%H:%M:%S+0:00')
    except Exception as e:
        print('ERROR:', e)

    try:
        annotations = json.loads(row[idx_annotations])
        subject_data = json.loads(row[idx_subject_data])
        return annotations, subject_data, row[idx_user_name].strip(), created_at
    except Exception as e:
        print('ERROR:', e)

    return None, None, None, None


def parse_subject_data(subject_data, logger):
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


def parse_annotations(annotations, logger):
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

        elif isinstance(answer, list):
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

        else:
            continue

    return parsed_annotations


def parse_csv(data, logger):
    first = True
    header_ids = {}

    collected_objects = {}
    valid_rows = 0

    csvreader = csv.reader(data, delimiter=',', quotechar='"', escapechar='\\')
    for row in csvreader:
        if first:
            first = False
            for i in range(len(row)):
                header_ids[row[i]] = i
            continue

        annotations, subject_data, user_name, created_at = parse_csv_row(
            row, header_ids, logger)
        if annotations is None:
            continue
        if subject_data is None:
            continue
        if user_name is None or user_name == '':
            user_name = '<unknown>'
        if created_at is None or created_at == '':
            created_at = None

        # parse signatur from subject_data
        signatur = parse_subject_data(subject_data, logger)
        if signatur is None:
            continue

        # parse answers from annotations
        answers = parse_annotations(annotations, logger)

        if not signatur in collected_objects:
            collected_objects[signatur] = {}
        if not user_name in collected_objects[signatur]:
            collected_objects[signatur][user_name] = {}
        collected_objects[signatur][user_name][created_at] = answers

        valid_rows += 1

    logger.info('parsed {0} objects from {1} csv rows'.format(
        len(collected_objects), valid_rows))

    return collected_objects
