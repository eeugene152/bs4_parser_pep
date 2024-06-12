from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException

MESSAGE_URL_FAILURE = ('Ошибка загрузки: {url}')
MESSAGE_TAG_NOT_FOUND = ('Не найден тег {tag} {attrs}')


def get_response(session, url):
    try:
        response = session.get(url, 'utf-8')
        return response
    except RequestException:
        raise ConnectionError(MESSAGE_URL_FAILURE.format(url=url))


def find_tag(soup, tag, attrs=None):
    # пока пытаюсь прокурить замечание..
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            MESSAGE_TAG_NOT_FOUND.format(tag=tag, attrs=attrs)
        )
    return searched_tag


def cook_soup(session, url):
    return BeautifulSoup(get_response(session, url).text, features='lxml')
