import logging
import re
import requests_cache

from bs4 import BeautifulSoup
from collections import defaultdict
from tqdm import tqdm
from urllib.parse import urljoin

from configs import configure_argument_parser, configure_logging
from outputs import control_output
from utils import get_response, find_tag

from constants import BASE_DIR, MAIN_DOC_URL, PEP_SITE_URL, EXPECTED_STATUS


MSG_STATUS_PEP_NOT_MATCHED = (
    'Несовпадающие статусы:'
    '{pep_link} '
    'Статус в карточке: {card_status}'
    'Ожидаемые статусы: {table_status}'
)


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )
    for section in sections_by_python:
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(sections_by_python, desc='Загрузка из кеша'):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = soup.find('dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    td_tags = soup.find_all('td')
    for td_tag in td_tags:
        if td_tag.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')}):
            pdf_a4_tag = td_tag.find(
                'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
            )
            archive_url = urljoin(downloads_url, pdf_a4_tag['href'])
    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEP_SITE_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    status_dict_count = defaultdict(int)
    error_list = []
    results = []
    pattern = r'^\d+$'

    main_div = soup.find('section', attrs={'id': 'numerical-index'})
    tr_tags = main_div.find_all('tr')
    for tr_tag in tqdm(tr_tags):
        for abbr_tag in tr_tag.find_all('abbr'):
            abbr_status_short = abbr_tag.text[1:]
        a_tags = tr_tag.find_all(
            'a', attrs={'class': 'pep reference internal'}
        )
        for a_tag in a_tags:
            if re.search(pattern, a_tag.text):
                continue
            pep_link = urljoin(PEP_SITE_URL, a_tag['href'])
            response = get_response(session, pep_link)
            soup = BeautifulSoup(response.text, features='lxml')
            dt_status_head_tag = soup.find(
                lambda tag: tag.name == 'dt' and 'Status' in tag.text
            )
            dt_status_tag = dt_status_head_tag.next_sibling.next_sibling

            try:
                if dt_status_tag.text not in EXPECTED_STATUS[
                    abbr_status_short
                ]:
                    error_list.append(
                        MSG_STATUS_PEP_NOT_MATCHED.format(
                            pep_link=pep_link,
                            card_status=dt_status_tag.text,
                            table_status=EXPECTED_STATUS[abbr_status_short]
                        )
                    )
                else:
                    status_dict_count[dt_status_tag.text] += 1
                    status_dict_count['Total'] += 1
            except KeyError:
                logging.info(
                    f'Неизвестный статус {a_tag["href"]} '
                    f'в таблице Numerical Index'
                )

    for error in error_list:
        logging.info(error)
    results = [('Статус', 'Количество')]
    total_item = status_dict_count.pop('Total')
    results.extend(sorted(status_dict_count.items()))
    results.append(('Total', total_item))
    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
