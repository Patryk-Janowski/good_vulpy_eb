import json
import base64
import geoip2.database
from cryptography.fernet import Fernet


key = 'JHtM1wEt1I1J9N_Evjwqr3yYauXIqSxYzFnRhcf0ZG0='
fernet = Fernet(key)
ttl = 7200  # seconds
reader = geoip2.database.Reader('GeoLite2-Country.mmdb')


def getcountry(request):

    country = 'XX'  # For local connections

    try:
        geo = reader.country(request.remote_addr)
        country = geo.country.iso_code
    except Exception:
        pass

    return country


def create(request, response, username):

    country = getcountry(request)
    encrypted_session_info = fernet.encrypt(
        (f"{username}|{country}").encode('utf-8'))
    safe_for_cookie = base64.b64encode(encrypted_session_info).decode('utf-8')
    response.set_cookie('vulpy_session', safe_for_cookie)

    return response


def load(request):

    safe_for_cookie = request.cookies.get('vulpy_session')

    if safe_for_cookie is None:
        return {}

    try:
        encrypted_session_info = base64.b64decode(safe_for_cookie)
        session_info = fernet.decrypt(encrypted_session_info).decode()
        username, country = session_info.split('|')
    except Exception as e:
        print(e)
        return {}

    if country == getcountry(request.remote_addr):
        return {'username': username, 'country': country}
    else:
        return {}


def destroy(response):
    response.set_cookie('vulpy_session', '', expires=0)
    return response
