def unread_notifications(request):
    if request.user.is_authenticated:
        return {"unread_count": request.user.notifications.filter(is_read=False).count()}
    return {}


_ASSET_VERSION = str(int(__import__("time").time()))


def assets(request):
    """Changes on every server start so browsers never serve stale CSS/JS."""
    return {"asset_v": _ASSET_VERSION}
