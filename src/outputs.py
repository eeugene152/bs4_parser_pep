import csv
import datetime as dt
import logging

from prettytable import PrettyTable

from constants import (
    BASE_DIR, CHOICE_FILE,
    CHOICE_PRETTY, DATETIME_FORMAT, RESULTS_PART
)


RESULTS_SAVED_TO_FILE = ('Результаты сохранены в файл: {file_path}')


def default_output(results, *args):
    for row in results:
        print(*row)


def pretty_output(results, *args):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / RESULTS_PART
    results_dir.mkdir(exist_ok=True)

    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_path = results_dir / f'{parser_mode}_{now_formatted}.csv'

    with open(file_path, 'w', encoding='utf-8') as f:
        csv.writer(f, dialect=csv.unix_dialect).writerows(results)
    logging.info(RESULTS_SAVED_TO_FILE.format(file_path=file_path))


OUTPUT_VARIANTS = {
    CHOICE_PRETTY: pretty_output,
    CHOICE_FILE: file_output,
    None: default_output
}


def control_output(results, cli_args):
    OUTPUT_VARIANTS.get(cli_args.output)(results, cli_args)
