import functools
from urlparse import urlunparse

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse as simple_reverse


DEFAULT_URL_SCHEME = getattr(settings, 'DEFAULT_URL_SCHEME', '')
DEFAULT_URL_SCHEMES = getattr(settings, 'DEFAULT_URL_SCHEMES', {})
DEFAULT_SUBDOMAIN = getattr(settings, 'DEFAULT_SUBDOMAIN', None)
UNSET = object()


def get_default_urls_group():
    """Find URLCONFS with same urls, split them by groups,
    find default group with None
    """
    res = {}
    for key, value in settings.SUBDOMAIN_URLCONFS.items():
        res.setdefault(value, []).append(key)
    return [val for value in res.values() for val in value
            if None in value and val is not None]


def current_site_domain():
    return Site.objects.get_current().domain


get_domain = current_site_domain
default_url_group = get_default_urls_group()


def get_url_subdomain(request, subdomain=UNSET):
    """get subdomain to get reverse url.
    If subdomain is UNSET then try get sundomain attribute from request.
    If subdomain is '' then try get sundomain attribute from request
    and check if there is same subdomain in settings.SUBDOMAIN_URLCONFS in
    a group with None(default)

    SUBDOMAIN_URLCONFS = {
        None: 'base.urls',
        'www': 'base.urls',
        'api': 'api.urls',
    }
    So, www is in same group with None, those are default domain urls
    Else - just return subdomain
    """
    if (subdomain and subdomain is not UNSET) or subdomain is None:
        return subdomain
    request_subdomain = getattr(request, 'subdomain', None)\
        if request is not None else None
    if request_subdomain is None:
        return DEFAULT_SUBDOMAIN
    if subdomain is UNSET:
        # get domain from request
        return request_subdomain
    elif subdomain == '':
        # check either domain from request is in default group, if
        # no - return DEFAULT_URL
        if request_subdomain in default_url_group:
            return request_subdomain
    return DEFAULT_SUBDOMAIN


def urljoin(domain, path=None, scheme=None, subdomain=None):
    """
    Joins a domain, path and scheme part together, returning a full URL.

    :param domain: the domain, e.g. ``example.com``
    :param path: the path part of the URL, e.g. ``/example/``
    :param scheme: the scheme part of the URL, e.g. ``http``, defaulting to the
        value of ``settings.DEFAULT_URL_SCHEME``
    :returns: a full URL
    """
    if scheme is None:
        scheme = DEFAULT_URL_SCHEMES.get(subdomain) or DEFAULT_URL_SCHEME or ''

    return urlunparse((scheme, domain, path or '', None, None, None))


def reverse(viewname, subdomain=None, scheme=None, args=None, kwargs=None,
        current_app=None):
    """
    Reverses a URL from the given parameters, in a similar fashion to
    :meth:`django.core.urlresolvers.reverse`.

    :param viewname: the name of URL
    :param subdomain: the subdomain to use for URL reversing
    :param scheme: the scheme to use when generating the full URL
    :param args: positional arguments used for URL reversing
    :param kwargs: named arguments used for URL reversing
    :param current_app: hint for the currently executing application
    """
    urlconf = settings.SUBDOMAIN_URLCONFS.get(subdomain)

    domain = get_domain()
    if subdomain is not None:
        domain = '%s.%s' % (subdomain, domain)

    path = simple_reverse(viewname, urlconf=urlconf, args=args, kwargs=kwargs,
        current_app=current_app)
    return urljoin(domain, path, scheme=scheme, subdomain=subdomain)


#: :func:`reverse` bound to insecure (non-HTTPS) URLs scheme
insecure_reverse = functools.partial(reverse, scheme='http')

#: :func:`reverse` bound to secure (HTTPS) URLs scheme
secure_reverse = functools.partial(reverse, scheme='https')

#: :func:`reverse` bound to be relative to the current scheme
relative_reverse = functools.partial(reverse, scheme='')
