from setuptools import setup, find_packages
import os
here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='SlackBot',
    version='1.0',
    packages=find_packages(),
    package_data={'src': ['absent.txt', 'src/absent.txt'],},
    author='Michael Spear',
    author_email='michael.spear@navegate.com',
    install_requires = ['slackclient', 'SQLAlchemy', 'jira'],
    tests_require = ['pytest'],
    setup_requires = ['pytest-runner'],
    url=''
)
