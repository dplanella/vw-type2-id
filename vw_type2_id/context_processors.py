from django.conf import settings


def git_commit(request):
    """Commit the running image was built from, for the footer."""
    return {'git_commit': settings.GIT_COMMIT}
