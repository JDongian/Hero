import os
import glob
import shutil
import pickle
import logging
import spell
import hero

DEFAULT_LOGIN_CONF = "login.conf"
DEFAULT_TMP_DIR = "/tmp/hero/"
SAVE_FILE = "save.p"


def _is_documentation(fname):
    # TODO: be broader
    _, ext = os.path.splitext(fname)
    return ext in ('.md', '.rst')


def _find_doc_file_paths(directory):
    docs = []

    for fname in glob.iglob(os.path.join(directory, '**/*'), recursive=True):
        if _is_documentation(fname):
            logging.debug("found documentation at {}".format(fname))
            docs.append(fname)

    return docs


def apply_spellcheck(prj_path):
    # find all documentation files in the repo
    file_changes = {}

    doc_paths = _find_doc_file_paths(prj_path)
    logging.debug("({}) documentation files found".format(len(doc_paths)))

    # TODO: filecmp or file size limits
    # spell check all the documents in the repo
    for fname in doc_paths:
        diff = spell.spellcheck(fname)
        # save any diffs generated
        if diffs:
            # WARNING: absolute path used
            file_changes[fname] = diff

    return file_changes


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity",
                        action="count", default=0,
                        help="increase output verbosity")
    parser.add_argument("-c", "--config",
                        default=DEFAULT_LOGIN_CONF,
                        help="login configuration file path")
    parser.add_argument("-d", "--directory",
                        default=DEFAULT_TMP_DIR,
                        help="temporary working directory")
    args = parser.parse_args()


    if args.verbosity == 0:
        logging.basicConfig(level=logging.CRITICAL)
    elif args.verbosity == 1:
        logging.basicConfig(level=logging.ERROR)
    elif args.verbosity == 2:
        logging.basicConfig(level=logging.WARN)
    elif args.verbosity == 3:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)


    # read file or prompt password
    user, limit = hero.login(args.config)
    logging.info("{} remaining requests for the hour.".format(limit))


    # TODO: logging decorators
    #def _debug_cb(user, repo):
    #    logging.info("checking repo {}/{}".format(user.login,
    #                                              repo.name))

    def update_spelling(user, repo):
        hero.auto_pr(user, repo, args.directory,
                     apply_spellcheck,
                     cmsg="automatic spellcheck",
                     cargs={
                         'title': "fix spelling",
                         'body': "automatic spelling fixes"})

    # traverse through (nearly) all repositories on Github
    hero.traverse_repos(user, update_spelling, True)


    # clean up
    try:
        shutil.rmtree(args.directory)
    except FileNotFoundError:
        pass
