#!/home/joshua/venv/bin/python
import os
import sys
import glob
import shutil
import pickle
import configparser
import logging
from github import Github
from getpass import getpass
from git import Repo

LOGIN_CONF = "login.conf"
CLONE_DIR = "/tmp/hero/"
SAVE_FILE = "save.p"
LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


def login(username, password):
    g = Github(username, password)
    return g.get_user(), g.get_rate_limit().rate.remaining


if __name__ == "__main__":
    if len(sys.argv) > 1:
        level_name = sys.argv[1]
        level = LEVELS.get(level_name, logging.NOTSET)
        logging.basicConfig(level=level)

    if os.path.isfile(LOGIN_CONF):
        config = configparser.ConfigParser()
        config.read(LOGIN_CONF)
        usr, pwd = config['login']['username'], config['login']['password']
    else:
        usr, pwd = input("Username: "), getpass("Password: ")

    user, limit = login(usr, pwd)
    logging.info("{} remaining requests for the hour.".format(limit))

    # for...
    j = user.get_repos().get_page(2)[14]

    # in the loop
    docs = []

    shutil.rmtree(CLONE_DIR)
    Repo.clone_from(j.clone_url, CLONE_DIR)
    for fname in glob.iglob(os.path.join(CLONE_DIR, '/**/*', recursive=True):
        if is_documentation(fname):
            docs.append(fname)

    for doc in docs:
        pass

    #endfor




    #targets = list(user.get_following())

    #ids = set()
    #traversed = { user.id }

    #with open(SAVE_FILE, "rb") as fp:
    #    ids = pickle.load(fp)
    #ids.discard(user.id)

    #print(user, limit, targets, traversed)
