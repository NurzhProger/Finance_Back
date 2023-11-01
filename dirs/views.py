from django.http import HttpResponse
from rest_framework import pagination
from rest_framework import response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json
from django.db.models import Q
from django.contrib.auth.models import User
from django.db import connection, transaction
from .models import *
from .serializer import *
from .shareModule import *
from rest_framework.authtoken.models import Token

class CustomPagination(pagination.LimitOffsetPagination):
    default_limit = 25  # Количество объектов на странице по умолчанию
    max_limit = 50     # Максимальное количество объектов на странице



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organizationlist(request):
    queryset = organization.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = organizationSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organizationitem(request, id):
    queryset = organization.objects.get(id=id)
    parent = queryset.child_organization
    serialparent = parent_organizationsSerializer(parent, many=True)
    serial = organizationSerializer(queryset, many=False)
    asd = serial.data
    asd["parent_organizations"] = serialparent.data
    return response.Response(asd)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def organizationsave(request):
    datastr = request.body
    data = json.loads(datastr)
    id = data['id']
    bin = data['bin']
    adress = data['adress']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']
    _budjet = data['_budjet']

    if id == 0:
        new = organization()
    else:
        new = organization.objects.get(id=id)
    new.bin = bin
    new.name_kaz = name_kaz
    new.name_rus = name_rus
    new.adress = adress
    new._budjet_id = _budjet['id']
    new.save()
    return HttpResponse('{"status":"Успешно добавлен родитель"}', content_type="application/json")


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def organizationdelete(request, id):
    try:
        orgitem = organization.objects.get(id=id)
        orgitem.deleted = not orgitem.deleted
        orgitem.save()
    except:
        return HttpResponse('{"status": "Ошибка удаления организации"}', content_type="application/json", status=400)

    queryset = organization.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = organizationSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budjetlist(request):
    queryset = budjet.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def parent_organization_add(request):
    datastr = request.body
    data = json.loads(datastr)
    id_org =  data['_organization_id']
    id_parent = data['_parent_id']
    date_object = datetime.strptime(data['_date'], '%d.%m.%Y %H:%M:%S')  
    _date = date_object
    newparent = parent_organizations()
    newparent._organization_id = id_org
    newparent._parent_id = id_parent
    newparent._date = _date
    newparent.save()
    return HttpResponse('{"id": ' + str(newparent.id) + ',  "status":"Успешно добавлен родитель"}', content_type="application/json")



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def parent_organization_del(request, id):
    try:
        orgitem = parent_organizations.objects.get(id=id)
        orgitem.delete()
    except:
        return HttpResponse('{"status": "Ошибка удаления организации"}', content_type="application/json", status=400)

    queryset = organization.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = organizationSerializer(paginated_queryset, many=True)
    return HttpResponse('{"status": "Успешно удален"}', content_type="application/json")



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def userlist(request):
    queryset = User.objects.all().order_by('username')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = userlistSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def useritem(request, id):
    queryset = User.objects.get(id=id)
    serial = useritemSerializer(queryset, many=False)

    try:
        profileobj = profile.objects.get(_user_id = id)
        _organization = {"id": profileobj._organization.id, "name_rus": profileobj._organization.name_rus}
    except:
        _organization = {"id": 0, "name_rus": "Выберите организацию"}

    asd = serial.data
    asd["password"] = ''
    asd["organization"] = _organization
    return response.Response(asd)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def usersave(request):
    datastr = request.body
    data = json.loads(datastr)

    try:
        with transaction.atomic():
            id = data['id']
            if id == 0:
                userobj = User()
                username =  data['username']
                userobj.username = username

            else:
                userobj = User.objects.get(id = id)

            first_name =  data['first_name']
            last_name =  data['last_name']
            email =  data['email']
            is_active =  data['is_active']

            userobj.first_name = first_name
            userobj.last_name = last_name
            userobj.email = email
            userobj.is_active = is_active
            if not data['password']=='':
                userobj.set_password(data['password'])
                Token.objects.filter(user_id = id).delete()
            userobj.save()

        
            try:
                profileobj = profile.objects.get(_user_id = id)
            except:
                profileobj = profile()
                profileobj._date_change = datetime.now()
            profileobj._user_id = userobj.id
            profileobj._organization_id = data['organization']['id']
            if not data['password']=='':
                profileobj.changepass = True
                profileobj._date_change = datetime.now()
            profileobj.save()

            

            return HttpResponse('{"status": "Пользователь сохранен"}', content_type="application/json")
    except Exception as err:
        print(err)
        return HttpResponse('{"status": "Ошибка сохранения"}', content_type="application/json", status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def changepass(request):
    datastr = request.body
    data = json.loads(datastr)

    if not data['first_password']==data['second_password']:
        return HttpResponse('{"status": "Пароли не совпадают"}', content_type="application/json", status=400)

    try:
        with transaction.atomic():
            userobj = User.objects.get(id = request.user.pk)
            userobj.set_password(data['first_password'])
            userobj.save()

            profileobj = profile.objects.get(_user_id = request.user.pk)
            profileobj.changepass = False
            profileobj._date_change = datetime.now()
            profileobj.save()

            Token.objects.filter(user_id = request.user.pk).delete()

            return HttpResponse('{"status": "Good"}', content_type="application/json", status=200)
    except Exception:
        return HttpResponse('{"status": "Ошибка сохранения"}', content_type="application/json", status=400)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def userdel(request, id):
    queryset = User.objects.get(id=id)
    queryset.delete()
    return HttpResponse('{"status": "Пользователь удален"}', content_type="application/json")



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getinfo(request):
    
    username = request.user
    try:
        qset = User.objects.get(username = username)
        userserial = useritemSerializer(qset)
        profserial = profileSerializer(qset.profile)
        logs = loginhistory.objects.filter(username = username).order_by('-id')[:5]
        logsserial = loginhistorySerializer(logs, many = True)
        roles = request.user.groups.all()
        rolesname = []
        for itm in roles:
            rolesname.append(itm.name)
        respon = {"user": userserial.data, "profile": profserial.data, "history":logsserial.data, "roles":rolesname}
        return response.Response(respon)
    except Exception as err:
        print(err)
        respon = '{"user": "Ошибка сервера"}'
        return HttpResponse(respon, content_type="application/json", status = 400)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cleartoken(request):
    user_id = request.user.pk
    return HttpResponse('{"detail": "token cleared", "changepass":"False"}', content_type="application/json")
    
    # Token.objects.filter(user_id = user_id).delete()
    # objs = loginhistory.objects.filter(username = request.user).order_by('-id')[:5]
    # err = 0
    # lasttime = datetime.now()

    # for itm in objs:
    #     if itm.status == 'error':
    #         err +=1
    #         lasttime = itm._date

    # raznica = (datetime.now() - lasttime).total_seconds()/60
    # if err>=5 and raznica<=2:
    #     return HttpResponse('{"detail": "Вы заблокированы на 2 минуты."}', content_type="application/json", status = 400)
        
    # profileobj = profile.objects.get(_user_id = user_id)

    # diff_days = (datetime.now() - profileobj._date_change).days
    # if diff_days>60:
    #     return HttpResponse('{"detail": "token cleared", "changepass":"True"}', content_type="application/json")
    # else:
    #     return HttpResponse('{"detail": "token cleared", "changepass":"' + str(profileobj.changepass) + '"}', content_type="application/json")



@api_view(['POST'])
def logineduser(request):
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or request.META.get('REMOTE_ADDR', '')
    datastr = request.body
    data = json.loads(datastr)
    username = data['username']
    status = data['status']
    _date = datetime.now()

    objs = loginhistory.objects.filter(username = username).order_by('-id')[:5]
    err = 0
    lasttime = datetime.now()

    for itm in objs:
        if itm.status == 'error':
            err +=1
            lasttime = itm._date


    raznica = (datetime.now() - lasttime).total_seconds()/60

    if err>=5 and raznica<=2:
        return HttpResponse('{"status": "Вы заблокированы на 2 минуты."}', content_type="application/json", status = 400)


    obj = loginhistory()
    obj.username = username
    obj.status = status
    obj._date = _date
    obj.client_ip = client_ip
    obj.save()

    if status ==  "error":
        respon = '{"status": "Ошибка логина или пароля"}'
        return HttpResponse(respon, content_type="application/json", status = 400)


    return HttpResponse('{"status": "Успешно"}', content_type="application/json", status = 200)





# ****************************************************************
# **************Сервисы справочников поступления******************
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def categorylist(request):
    queryset = category_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def categoryadd(request):

    datastr = request.body
    data = json.loads(datastr)
    code = data['code']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']
    if not code == '':
        try:
            obj = category_income.objects.get(code=code)
            exist = True
        except:
            exist = False

        if not exist:
            newcat = category_income()
            newcat.code = code
            newcat.name_kaz = name_kaz
            newcat.name_rus = name_rus
            newcat.save()
        else:
            return HttpResponse('{"status": "Категория с таким кодом уже существует"}', content_type="application/json", status=400)
    else:
        return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status=400)

    queryset = category_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def categoryedit(request):

    datastr = request.body
    data = json.loads(datastr)
    id = data['id']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']

    newcat = category_income.objects.get(id=id)
    newcat.name_kaz = name_kaz
    newcat.name_rus = name_rus
    newcat.save()

    queryset = category_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def categorydelete(request, id):
    try:
        newcat = category_income.objects.get(id=id)
        newcat.delete()
    except:
        return HttpResponse('{"status": "Ошибка удаления категории"}', content_type="application/json", status=400)

    queryset = category_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def classlist(request):
    queryset = class_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classadd(request):

    datastr = request.body
    data = json.loads(datastr)
    code = data['code']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']
    if not code == '':
        try:
            obj = class_income.objects.get(code=code)
            exist = True
        except:
            exist = False

        if not exist:
            newcat = class_income()
            newcat.code = code
            newcat.name_kaz = name_kaz
            newcat.name_rus = name_rus
            newcat.save()
        else:
            return HttpResponse('{"status": "Класс с таким кодом уже существует"}', content_type="application/json", status=400)
    else:
        return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status=400)

    queryset = class_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classedit(request):

    datastr = request.body
    data = json.loads(datastr)
    id = data['id']
    # code = data['code']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']

    newcat = class_income.objects.get(id=id)
    # newcat.code = code
    newcat.name_kaz = name_kaz
    newcat.name_rus = name_rus
    newcat.save()

    # if not code == '':
    #     try:
    #         obj = class_income.objects.get(code = code)
    #         exist = True
    #     except:
    #         exist = False

    #     if not exist:
    #         newcat = class_income.objects.get(id = id)
    #         newcat.code = code
    #         newcat.name_kaz = name_kaz
    #         newcat.name_rus = name_rus
    #         newcat.save()
    #     else:
    #         return HttpResponse('{"status": "Класс с таким кодом уже существует"}', content_type="application/json", status = 400)
    # else:
    #     return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status = 400)

    queryset = class_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def classdelete(request, id):
    try:
        newcat = class_income.objects.get(id=id)
        newcat.delete()
    except:
        return HttpResponse('{"status": "Ошибка удаления категории"}', content_type="application/json", status=400)

    queryset = class_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def podclasslist(request):
    queryset = podclass_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def podclassadd(request):

    datastr = request.body
    data = json.loads(datastr)
    code = data['code']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']
    if not code == '':
        try:
            obj = podclass_income.objects.get(code=code)
            exist = True
        except:
            exist = False

        if not exist:
            newcat = podclass_income()
            newcat.code = code
            newcat.name_kaz = name_kaz
            newcat.name_rus = name_rus
            newcat.save()
        else:
            return HttpResponse('{"status": "Подкласс с таким кодом уже существует"}', content_type="application/json", status=400)
    else:
        return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status=400)

    queryset = podclass_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def podclassedit(request):

    datastr = request.body
    data = json.loads(datastr)
    id = data['id']
    # code = data['code']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']

    newcat = podclass_income.objects.get(id=id)
    # newcat.code = code
    newcat.name_kaz = name_kaz
    newcat.name_rus = name_rus
    newcat.save()

    # if not code == '':
    #     try:
    #         obj = podclass_income.objects.get(code = code)
    #         exist = True
    #     except:
    #         exist = False

    #     if not exist:
    #         newcat = podclass_income.objects.get(id = id)
    #         newcat.code = code
    #         newcat.name_kaz = name_kaz
    #         newcat.name_rus = name_rus
    #         newcat.save()
    #     else:
    #         return HttpResponse('{"status": "Класс с таким кодом уже существует"}', content_type="application/json", status = 400)
    # else:
    #     return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status = 400)

    queryset = podclass_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def podclassdelete(request, id):
    try:
        newcat = podclass_income.objects.get(id=id)
        newcat.delete()
    except:
        return HttpResponse('{"status": "Ошибка удаления категории"}', content_type="application/json", status=400)

    queryset = podclass_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def specinclist(request):
    queryset = spec_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def specincadd(request):

    datastr = request.body
    data = json.loads(datastr)
    code = data['code']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']
    if not code == '':
        try:
            obj = spec_income.objects.get(code=code)
            exist = True
        except:
            exist = False

        if not exist:
            newcat = spec_income()
            newcat.code = code
            newcat.name_kaz = name_kaz
            newcat.name_rus = name_rus
            newcat.save()
        else:
            return HttpResponse('{"status": "Подкласс с таким кодом уже существует"}', content_type="application/json", status=400)
    else:
        return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status=400)

    queryset = spec_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def specincedit(request):

    datastr = request.body
    data = json.loads(datastr)
    id = data['id']
    # code = data['code']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']

    newcat = spec_income.objects.get(id=id)
    # newcat.code = code
    newcat.name_kaz = name_kaz
    newcat.name_rus = name_rus
    newcat.save()

    # if not code == '':
    #     try:
    #         obj = spec_income.objects.get(code = code)
    #         exist = True
    #     except:
    #         exist = False

    #     if not exist:
    #         newcat = spec_income.objects.get(id = id)
    #         newcat.code = code
    #         newcat.name_kaz = name_kaz
    #         newcat.name_rus = name_rus
    #         newcat.save()
    #     else:
    #         return HttpResponse('{"status": "Класс с таким кодом уже существует"}', content_type="application/json", status = 400)
    # else:
    #     return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status = 400)

    queryset = spec_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def specincdelete(request, id):
    try:
        newcat = spec_income.objects.get(id=id)
        newcat.delete()
    except:
        return HttpResponse('{"status": "Ошибка удаления категории"}', content_type="application/json", status=400)

    queryset = spec_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def classificationinclist(request):
    try:
        search = request.GET['search']
    except:
        search = ''
    queryset = classification_income.objects.filter(Q(code__icontains=search)|Q(name_rus__icontains=search))

    # queryset = classification_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = classificatinIncSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def classificationincitem(request, id):
    queryset = classification_income.objects.get(id=id)
    serial = classificatinIncDetailSerializer(queryset)
    return response.Response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classificationincadd(request):

    datastr = request.body
    data = json.loads(datastr)

    category = data['_category_id']
    classs = data['_classs_id']
    podclass = data['_podclass_id']
    spec = data['_spec_id']

    try:
        catobj = category_income.objects.get(id=category)
        clasobj = class_income.objects.get(id=classs)
        podclobj = podclass_income.objects.get(id=podclass)
        specobj = spec_income.objects.get(id=spec)

        record = classification_income()
        record._category_id = category
        record._classs_id = classs
        record._podclass_id = podclass
        record._spec_id = spec

        record.code = catobj.code + clasobj.code + '-' + podclobj.code + specobj.code
        record.name_rus = specobj.name_rus
        record.name_kaz = specobj.name_kaz
        record.save()
    except:
        return HttpResponse('{"status": "Ошибка добавления классификации по поступлениям. Неверные данные"}', content_type="application/json", status=400)

    queryset = classification_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classificationincedit(request):

    datastr = request.body
    data = json.loads(datastr)

    id = data['id']
    category = data['_category_id']
    classs = data['_classs_id']
    podclass = data['_podclass_id']
    spec = data['_spec_id']

    try:
        catobj = category_income.objects.get(id=category)
        clasobj = class_income.objects.get(id=classs)
        podclobj = podclass_income.objects.get(id=podclass)
        specobj = spec_income.objects.get(id=spec)

        record = classification_income.objects.get(id=id)
        record._category_id = category
        record._classs_id = classs
        record._podclass_id = podclass
        record._spec_id = spec

        record.code = catobj.code + clasobj.code + '-' + podclobj.code + specobj.code
        record.name_rus = specobj.name_rus
        record.name_kaz = specobj.name_kaz
        record.save()
    except:
        return HttpResponse('{"status": "Ошибка изменения классификации по поступлениям. Неверные данные"}', content_type="application/json", status=400)

    queryset = classification_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def classificationincdelete(request, id):
    try:
        newcat = classification_income.objects.get(id=id)
        newcat.delete()
    except:
        return HttpResponse('{"status": "Ошибка удаления классификации поступления"}', content_type="application/json", status=400)

    queryset = classification_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def typeincdoclist(request):
    queryset = type_izm_doc.objects.all()
    serial = typedocSerializer(queryset, many=True)
    return response.Response(serial.data)





# ****************************************************************
# ****************Сервисы справочников расхода********************
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def funcgrouplist(request):
    queryset = funcgroup.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def funcpodgrouplist(request):
    queryset = funcpodgroup.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def abplist(request):
    queryset = abp.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programlist(request):
    queryset = program.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def podprogramlist(request):
    queryset = podprogram.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fkrlist(request):
    try:
        search = request.GET['search']
    except:
        search = ''
    queryset = fkr.objects.filter(Q(code__icontains=search)|Q(name_rus__icontains=search))

    # queryset = fkr.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def specexplist(request):
    queryset = spec_exp.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fkrupdate(request):
    workbook = fkrreadxls()
    return HttpResponse('{"status": "Загружены ФКР"}', content_type="application/json", status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ekrupdate(request):
    workbook = ekrreadxls()
    return HttpResponse('{"status": "Загружены ЭКР"}', content_type="application/json", status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inc_dir_import(request):
    workbook = inc_dir_import_xls()
    return HttpResponse('{"status": "Загружены спр по доходам"}', content_type="application/json", status=200)



