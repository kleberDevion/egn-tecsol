_online = {}


def mark_online(user_id, sid):
    _online.setdefault(user_id, set()).add(sid)


def mark_offline_by_sid(sid):
    for user_id, sids in list(_online.items()):
        sids.discard(sid)
        if not sids:
            del _online[user_id]


def get_online_user_ids():
    return set(_online.keys())
