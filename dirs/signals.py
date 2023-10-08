from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver
import datetime
from .models import loginhistory
from django.http import HttpResponse

@receiver(user_logged_in)
def before_user_logged_in(sender, request, user, **kwargs):
     # Получаем текущий токен пользователя
    # current_token = user.auth_token
    print(user)


@receiver(user_logged_in)
def after_user_logged_in(sender, request, user, **kwargs):
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR', '')
    _date = datetime.datetime.now()
    objs = loginhistory.objects.filter(username = user.username).order_by('-id')[:5]

    err = 0
    lasttime = datetime.datetime.now()

    for itm in objs:
        if itm.status == 'error':
            err +=1
            lasttime = itm._date


    raznica = (datetime.datetime.now() - lasttime).total_seconds()/60

    if err>=5 and raznica<=2:
        a = 1/0
        return HttpResponse('{"status": "Вы заблокированы на 2 минуты."}', content_type="application/json", status = 400)
    else:
        obj = loginhistory()
        obj.username = user.username
        obj.status = "ok"
        obj._date = _date
        obj.client_ip = client_ip
        obj.save()


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR', '')
    _date = datetime.datetime.now()
    objs = loginhistory.objects.filter(username = credentials['username']).order_by('-id')[:5]

    err = 0
    lasttime = datetime.datetime.now()

    for itm in objs:
        if itm.status == 'error':
            err +=1
            lasttime = itm._date


    raznica = (datetime.datetime.now() - lasttime).total_seconds()/60

    if err>=5 and raznica<=2:
        return HttpResponse('{"status": "Вы заблокированы на 2 минуты."}', content_type="application/json", status = 400)

    obj = loginhistory()
    obj.username = credentials['username']
    obj.status = "error"
    obj._date = _date
    obj.client_ip = client_ip
    obj.save()
    


