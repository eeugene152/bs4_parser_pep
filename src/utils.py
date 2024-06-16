from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException

MESSAGE_CONNECTION_ERROR = ('Ошибка подключения: {error}')
MESSAGE_TAG_NOT_FOUND = ('Не найден тег {tag} {attrs}')
MESSAGE_URL_FAILURE = ('Ошибка загрузки: {url}')


def get_response(session, url, coding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = coding
        return response
    except RequestException as error:
        raise ConnectionError(MESSAGE_CONNECTION_ERROR.format(error=error))


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            MESSAGE_TAG_NOT_FOUND.format(tag=tag, attrs=attrs)
        )
    return searched_tag


def cook_soup(session, url, features='lxml'):
    return BeautifulSoup(get_response(session, url).text, features)
