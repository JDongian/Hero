import os
import configparser
from getpass import getpass
from github import Github
from git import Repo


def _get_creds(conf):
    """Get credentials from a file or stdin.
    """
    if conf and os.path.isfile(conf):
        config = configparser.ConfigParser()
        config.read(conf)
        usr, pwd = config['login']['username'], config['login']['password']
    else:
        usr, pwd = input("Username: "), getpass("Password: ")
    return usr, pwd


def login(conf=None):
    """Authenticate with Github using their API (for a higher rate limit).
    """
    g = Github(*_get_creds(conf))
    limit = g.get_rate_limit().rate.remaining
    return g.get_user(), limit


def _depaginate(pagable):
    """This extension of the Github API hides pagination handling for a
    pagable object.
    This function returns a generator that is per-page lazy.
    """
    results = []
    page = 0
    buf = None

    # the github api is weird
    while buf == None or len(buf) > 0:
        buf = pagable.get_page(page)
        page += 1
        for e in buf:
            yield e


def traverse_repos(root, cb, skip=False):
    """Traverse repositories of github using the Github API.
    Runs cb on each user's repositories.
    If skip is True, then that user's repositories are not processed.
    """
    # convert the repo callback to a user callback
    def _user_cb(user):
        for repo in _depaginate(user.get_repos()):
            cb(user, repo)

    traverse_users(root, _user_cb, skip)


def traverse_users(root, cb, skip, visited=set()):
    """Traverse Github users breadth-first using the Github API.
    Runs cb on each user.
    If skip is True, then that user's repositories are not processed.
    """
    # avoid cycles
    visited.add(root.login)

    if not skip:
        cb(root)

    for user in _depaginate(root.get_following()):
        if not user.login in visited:
            traverse_users(user, cb, False)


def apply_diff(filename, diff):
    """Apply a diff to a file.
    """
    # TODO
    with open(filename, 'w') as fp:
        fp.write(diff)


def clone(repo, path):
    """Clone a given repository object to the specified path.
    """
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass
    finally:
        logging.debug("cloning {}".format(repo.clone_url))
        repo_local = Repo.clone_from(repo.clone_url, path)


def commit_and_pr(local, remote,
                  username, documents,
                  cmsg="auto", cargs={}):
    local.index.add(documents)
    local.index.commit(cmsg)

    local.remote('origin').push()

    args_pr = {'title': "automatic PR",
               'body': "automatically generated pull request",
               'head': "{}:master".format(username),
               'base': "master"}
    args_pr.update(cargs)

    logging.debug("making PR")
    remote.create_pull(**args_pr)


def auto_pr(user, repo_remote, work_path, updater, cmsg="auto", cargs={}):
    """Clone a repository, check for changes to be made, then fork and make a
    PR if needed.
    Runs updater on repository path, expecting a list of file diffs.
    """
    # clone original repository
    clone(repo_remote, work_path)

    # determine changes
    file_changes = updater(work_path)

    # fork repo if diffs generated
    if file_changes:
        repo_fork = user.create_fork(repo_remote)

        # clone forked repository
        clone(repo_fork, work_path)

        for name, diff in file_changes.items():
            # apply changes to file
            apply_diff(filename, diff)

        # commit and PR
        if repo_fork.index.diff(None): # TODO: retest the need for this
            commit_and_pr(repo_fork, repo_remote,
                          user.login, list(file_changes.keys()),
                          cmsg, cargs)
            # clean up
            repo_fork.delete()
