from pathlib import Path
from urllib.parse import urljoin


CHOICE_FILE = 'file'
CHOICE_PRETTY = 'pretty'
DATETIME_FORMAT = '%Y-%m-%d_%H-%M-%S'
DOWNLOADS_DIR_NAME = 'downloads'
DOWNLOAD_URL_PART = 'download.html'
LOG_DIR_NAME = 'logs'
LOG_FILE_NAME = 'parser.log'
RESULTS_PART = 'results'
WHATS_NEW_URL_PART = 'whatsnew/'

BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / DOWNLOADS_DIR_NAME
LOG_DIR = BASE_DIR / LOG_DIR_NAME
LOG_FILE = LOG_DIR / LOG_FILE_NAME
RESULTS_DIR = BASE_DIR / RESULTS_PART

MAIN_DOC_URL = 'https://docs.python.org/3/'
PEP_SITE_URL = 'https://peps.python.org/'
DOWNLOADS_URL = urljoin(MAIN_DOC_URL, DOWNLOAD_URL_PART)
WHATS_NEW_URL = urljoin(MAIN_DOC_URL, WHATS_NEW_URL_PART)

EXPECTED_STATUS = {
    'A': ['Active', 'Accepted'],
    'D': ['Deferred'],
    'F': ['Final'],
    'P': ['Provisional'],
    'R': ['Rejected'],
    'S': ['Superseded'],
    'W': ['Withdrawn'],
    '': ['Draft', 'Active'],
}
