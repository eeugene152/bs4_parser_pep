import logging
import re
from collections import defaultdict
from urllib.parse import urljoin

import requests_cache
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import cook_soup, get_response, find_tag
from constants import (BASE_DIR, EXPECTED_STATUS, DOWNLOADS_URL,
                       MAIN_DOC_URL, PEP_SITE_URL, WHATS_NEW_URL)

MESSAGE_STATUS_PEP_NOT_MATCHED = ('Несовпадающие статусы:'
                                  '{pep_link} '
                                  'Статус в карточке: {card_status}'
                                  'Ожидаемые статусы: {table_status}')
ARCHIVE_LOADED_SAVED = ('Архив был загружен и сохранён: {archive_path}')
UNKNOWN_STATUS = ('Неизвестный статус {a_tag_link} '
                  'в таблице Numerical Index')
MESSAGE_COMMAND_ARGUMENTS = ('Аргументы командной строки: {args}.')
MESSAGE_PARSER_LAUNCHED = ('Парсер запущен!')
MESSAGE_PARSER_FINISHED = ('Парсер завершил работу.')
PARSER_FAILURE = ('Ошибка работы программы: {error}')


def whats_new(session):
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]

    for section in tqdm(cook_soup(session, WHATS_NEW_URL).select_one(
            '#what-s-new-in-python div.toctree-wrapper'
            ).select('li.toctree-l1'), desc='Загрузка из кеша'):

        version_link = urljoin(WHATS_NEW_URL, section.find('a')['href'])
        soup = cook_soup(session, version_link)
        results.append(
            (version_link,
             find_tag(soup, 'h1').text,
             find_tag(soup, 'dl').text.replace('\n', ' '))
        )

    return results


def latest_versions(session):
    sidebar = find_tag(
        cook_soup(
            session, MAIN_DOC_URL
        ), 'div', attrs={'class': 'sphinxsidebarwrapper'}
    )
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise KeyError('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((a_tag['href'], version, status))
    return results


def download(session):
    pdf_a4_tag = find_tag(
        cook_soup(session, DOWNLOADS_URL),
        'a',
        {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    archive_url = urljoin(DOWNLOADS_URL, pdf_a4_tag['href'])
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / archive_url.split('/')[-1]
    # почему-то этот вариант не проходит тесты
    # DOWNLOADS_DIR.mkdir(exist_ok=True)
    # archive_path = DOWNLOADS_DIR / archive_url.split('/')[-1]
    with open(archive_path, 'wb') as file:
        file.write(get_response(session, archive_url).content)
    logging.info(ARCHIVE_LOADED_SAVED.format(archive_path=archive_path))


def pep(session):  # noqa: C901
    status_dict_count = defaultdict(int)
    error_list = []
    results = []
    pattern = r'^\d+$'

    main_div = cook_soup(
        session, PEP_SITE_URL
    ).find('section', attrs={'id': 'numerical-index'})
    tr_tags = main_div.find_all('tr')
    for tr_tag in tqdm(tr_tags):
        abbr_status_short = find_tag(tr_tag, 'abbr').text[1:]
        a_tags = tr_tag.find_all(
            'a', attrs={'class': 'pep reference internal'}
        )
        for a_tag in a_tags:
            if re.search(pattern, a_tag.text):
                continue
            pep_link = urljoin(PEP_SITE_URL, a_tag['href'])
            try:
                soup = cook_soup(session, pep_link)
            except ConnectionError as error:
                error_list.append(error)
                continue

            dt_status_head_tag = soup.find(
                lambda tag: tag.name == 'dt' and 'Status' in tag.text
            )
            dt_status_tag = dt_status_head_tag.next_sibling.next_sibling

            try:
                if dt_status_tag.text not in EXPECTED_STATUS[
                    abbr_status_short
                ]:
                    error_list.append(
                        MESSAGE_STATUS_PEP_NOT_MATCHED.format(
                            pep_link=pep_link,
                            card_status=dt_status_tag.text,
                            table_status=EXPECTED_STATUS[abbr_status_short]
                        )
                    )
                else:
                    status_dict_count[dt_status_tag.text] += 1
            except KeyError:
                error_list.append(
                    UNKNOWN_STATUS.format(a_tag_link=a_tag['href'])
                )
    # не нашел пока.. туплю. может быть помощь зала? или 50 на 50? :))
    for error in error_list:
        logging.info(error)
    results.extend(sorted(status_dict_count.items()))
    dict_final = dict(results)
    return [
            ('Статус', 'Количество'),
            *dict_final.items(),
            ('Total', sum(dict_final.values())),
        ]


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info(MESSAGE_PARSER_LAUNCHED)

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(MESSAGE_COMMAND_ARGUMENTS.format(args=args))

    session = requests_cache.CachedSession()
    try:
        if args.clear_cache:
            session.cache.clear()

        parser_mode = args.mode
        results = MODE_TO_FUNCTION[parser_mode](session)

        if results is not None:
            control_output(results, args)
    except Exception as error:
        logging.exception(
            PARSER_FAILURE.format(error=error)
        )
    logging.info(MESSAGE_PARSER_FINISHED)


if __name__ == '__main__':
    main()
