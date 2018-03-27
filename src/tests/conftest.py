import pytest
import os
import shutil
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

collect_ignore = ['setup.py']

base_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '..', '..'))

if base_dir not in sys.path:
    sys.path.append(base_dir)

test_db_path = os.path.abspath(os.path.join(base_dir, 'tests', 'test_db.db'))
shutil.copy(os.path.join(base_dir, '..', 'sql_bot.db'), test_db_path)

@pytest.fixture
def TEST_CHANNEL():
    return 'C5ZMWUJR0'

@pytest.fixture(scope='module')
def session():
    engine = create_engine("sqlite:///" + test_db_path)
    s = Session(bind=engine)
    yield s
    print('CLOSING SESSION')
    s.close()
