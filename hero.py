import pickle
from github import Github
from getpass import getpass

if __name__ == "__main__":
    g = Github(input("Username: "), getpass("Password: "))
    user = g.get_user()
    print("{} remaining requests for the hour."
            .format(g.get_rate_limit().rate.remaining))
    o = list(user.get_following())

    ids = set()
    traversed = { user.id }

    try:
        with open("save.p", "rb") as fp:
            ids = pickle.load(fp)
        ids.add(user.id)
        count = 0
        for following in o:
            ids.add(following.id)
            count += 1
            o.append(following)
            if (count > 40):
                break
    finally:
        with open("save.p", "wb") as fp:
            pickle.dump(ids, fp)

    print("done saving old followed users")

    while len(o) > 0: # basically never stop
        target = o.pop()
        if target.id in traversed:
            continue
        traversed.add(target.id)

        if (not target.id in ids):
            ids.add(target.id)

            name = target.name or str(target.id)
            print("FOLLOW: " + name)

            user.add_to_following(target)

            with open("save.p", "wb") as fp:
                pickle.dump(ids, fp)

        count = 0
        for follower in target.get_followers():
            o.append(follower)
            count += 1
            if (count > 20):
                break
    print("exhausted search (???)")
