from bs4 import BeautifulSoup
from requests import RequestException

from exceptions import ParserFindTagException

CONNECTION_ERROR = ('Ошибка подключения: {error} URL: {url}')
TAG_NOT_FOUND = ('Не найден тег {tag} {attrs}')


def get_response(session, url, coding='utf-8'):
    try:
        response = session.get(url)
        response.encoding = coding
        return response
    except RequestException as error:
        raise ConnectionError(
            CONNECTION_ERROR.format(
                error=error,
                url=url
            )
        )


def find_tag(soup, tag, attrs=None):
    searched_tag = soup.find(tag, attrs=(attrs or {}))
    if searched_tag is None:
        raise ParserFindTagException(
            TAG_NOT_FOUND.format(tag=tag, attrs=attrs)
        )
    return searched_tag


def cook_soup(session, url, features='lxml'):
    return BeautifulSoup(get_response(session, url).text, features)
