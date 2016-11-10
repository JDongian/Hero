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
import spell


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

# TODO: logger name
if len(sys.argv) > 1:
        level_name = sys.argv[1]
        level = LEVELS.get(level_name, logging.NOTSET)
        logging.basicConfig(level=level)


def _get_creds():
    if os.path.isfile(LOGIN_CONF):
        config = configparser.ConfigParser()
        config.read(LOGIN_CONF)
        usr, pwd = config['login']['username'], config['login']['password']
    else:
        usr, pwd = input("Username: "), getpass("Password: ")
    return usr, pwd


def login():
    g = Github(*_get_creds())
    limit = g.get_rate_limit().rate.remaining
    logging.info("{} remaining requests for the hour.".format(limit))
    return g.get_user(), limit


def _is_documentation(fname):
    # TODO: be broader
    _, ext = os.path.splitext(fname)
    return ext in ('.md', '.rst')


def _commit_and_pr(local, remote, username, documents):
    local.index.add(documents)
    local.index.commit("automated spellcheck")

    local.remote('origin').push()

    args_pr = {'title': "spelling fixes",
               'body': "automatically generated",
               'head': "{}:master".format(username),
               'base': "master"}
    remote.create_pull(**args_pr)


def spellcheck(repo_remote):
    # fork
    repo_fork = user.create_fork(repo_remote)

    # in the loop
    docs = []
    new_docs = dict()

    try:
        shutil.rmtree(CLONE_DIR)
    except FileNotFoundError:
        pass
    finally:
        logging.info("cloning repo from {}".format(repo_remote.clone_url))
        repo_local = Repo.clone_from(repo_fork.clone_url, CLONE_DIR)

    # find all documentation files in the repo
    for fname in glob.iglob(os.path.join(CLONE_DIR, '**/*'), recursive=True):
        if _is_documentation(fname):
            logging.info("found documentation at {}".format(fname))
            docs.append(fname)

    # spell check all the documents in the repo
    for fname in docs:
        with open(fname, 'rb') as fp:
            doc = fp.read().decode(errors='ignore')
        # TODO: lazy here
        logging.info("spell-checking file{}".format(fname))
        # TODO: rm double check
        new_docs[fname] = spell.correct(doc)
        if new_docs[fname] != doc:
            with open(fname, 'w') as fp:
                fp.write(new_docs[fname])
        else:
            logging.info("updating corpus...")
            spell.update_corpus(doc)
            # TODO: save corpus to pickle


    # commit and PR if changes were made
    if repo_local.index.diff(None):
        logging.info("changes detected -- making PR")
        _commit_and_pr(repo_local, repo_remote, user.login,
                       list(new_docs.keys()))


if __name__ == "__main__":
    user, _ = login()

    #repo_remote = user.get_followers().get_page(0)[0].get_repos().get_page(0)[11] # mcc
    for follower in user.get_followers().get_page(1):
        for repo_remote in follower.get_repos().get_page(0):
            logging.info("spell-checking repo {}/{}".format(follower.login,
                                                            repo_remote.name))
            spellcheck(repo_remote)
