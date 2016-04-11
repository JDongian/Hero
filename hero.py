#!/home/joshua/venv/bin/python
import pickle
from github import Github
from getpass import getpass
from sys import argv

SAVE_FILE = "save.p"


def search(targets):
    target = targets.pop()
    if target.id in traversed:
        return
    traversed.add(target.id)

    if (not target.id in ids):
        ids.add(target.id)

        name = target.name or str(target.id)
        print("FOLLOW: " + name)

        user.add_to_following(target)

        with open(SAVE_FILE, "wb") as fp:
            pickle.dump(ids, fp)

    count = 0
    for follower in target.get_followers():
        targets.append(follower)
        count += 1
        # prevent timeouts on people with too many followers (?)
        if (count > 50):
            break
    count = 0
    for following in target.get_following():
        targets.append(follower)
        count += 1
        # prevent timeouts on people with too many following (?)
        if (count > 50):
            break

def get_user():
    if len(argv) > 2:
        g = Github(argv[1], argv[2])
    else:
        g = Github(input("Username: "), getpass("Password: "))
    return g.get_user(), g.get_rate_limit().rate.remaining


if __name__ == "__main__":
    user, limit = get_user()
    print("{} remaining requests for the hour."
            .format(limit))

    targets = list(user.get_following())

    ids = set()
    traversed = { user.id }

    try:
        with open(SAVE_FILE, "rb") as fp:
            ids = pickle.load(fp)
        ids.add(user.id)

        count = 0

        # TODO: have guarantees so this isn't needed
        for following in targets:
            ids.add(following.id)
            count += 1
            targets.append(following)
            if (count > 40):
                break
    finally:
        with open(SAVE_FILE, "wb") as fp:
            pickle.dump(ids, fp)

    print("done saving old followed users")

    while len(targets) > 0: # basically never stop
        try:
            search(targets)
        except:
            pass
    print("exhausted search (???)")
