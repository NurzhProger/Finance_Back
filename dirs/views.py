from django.http import HttpResponse
from rest_framework import pagination
from rest_framework import response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json
from .models import *
from .serializer import *
from .shareModule import *



class CustomPagination(pagination.LimitOffsetPagination):
    default_limit = 25  # Количество объектов на странице по умолчанию
    max_limit = 50     # Максимальное количество объектов на странице



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organizationlist(request):
    queryset = organization.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = organizationSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def organizationitem(request, id):
    queryset = organization.objects.get(id = id)
    # paginator = CustomPagination()
    # paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = organizationSerializer(queryset, many = False)
    return response.Response(serial.data)


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
    new._budjet_id = _budjet
    new.save()

    queryset = organization.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = organizationSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def organizationdelete(request, id):
    try:
        orgitem = organization.objects.get(id = id)
        orgitem.deleted =  not orgitem.deleted
        orgitem.save() 
    except:
        return HttpResponse('{"status": "Ошибка удаления организации"}', content_type="application/json", status = 400)

    queryset = organization.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = organizationSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budjetlist(request):
    queryset = budjet.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fkrupdate(request):
    workbook = fkrreadxls()
    return HttpResponse('{"status": "Загружены ФКР"}', content_type="application/json", status = 200) 



# ****************************************************************
# **************Сервисы справочников поступления******************
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def categorylist(request):
    queryset = category_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
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
            obj = category_income.objects.get(code = code)
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
            return HttpResponse('{"status": "Категория с таким кодом уже существует"}', content_type="application/json", status = 400) 
    else:
        return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status = 400) 

    queryset = category_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def categoryedit(request):

    datastr = request.body
    data = json.loads(datastr)
    id = data['id']
    name_kaz = data['name_kaz']
    name_rus = data['name_rus']

    newcat = category_income.objects.get(id = id)
    newcat.name_kaz = name_kaz
    newcat.name_rus = name_rus
    newcat.save()

    queryset = category_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def categorydelete(request, id):
    try:
        newcat = category_income.objects.get(id = id)
        newcat.delete() 
    except:
        return HttpResponse('{"status": "Ошибка удаления категории"}', content_type="application/json", status = 400)

    queryset = category_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def classlist(request):
    queryset = class_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
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
            obj = class_income.objects.get(code = code)
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
            return HttpResponse('{"status": "Класс с таким кодом уже существует"}', content_type="application/json", status = 400) 
    else:
        return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status = 400) 

    queryset = class_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
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

    newcat = class_income.objects.get(id = id)
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
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def classdelete(request, id):
    try:
        newcat = class_income.objects.get(id = id)
        newcat.delete() 
    except:
        return HttpResponse('{"status": "Ошибка удаления категории"}', content_type="application/json", status = 400)

    queryset = class_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def podclasslist(request):
    queryset = podclass_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
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
            obj = podclass_income.objects.get(code = code)
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
            return HttpResponse('{"status": "Подкласс с таким кодом уже существует"}', content_type="application/json", status = 400) 
    else:
        return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status = 400) 

    queryset = podclass_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
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

    newcat = podclass_income.objects.get(id = id)
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
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def podclassdelete(request, id):
    try:
        newcat = podclass_income.objects.get(id = id)
        newcat.delete() 
    except:
        return HttpResponse('{"status": "Ошибка удаления категории"}', content_type="application/json", status = 400)

    queryset = podclass_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def specinclist(request):
    queryset = spec_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
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
            obj = spec_income.objects.get(code = code)
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
            return HttpResponse('{"status": "Подкласс с таким кодом уже существует"}', content_type="application/json", status = 400) 
    else:
        return HttpResponse('{"status": "Поле код обязателен для заполнения"}', content_type="application/json", status = 400) 

    queryset = spec_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
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

    newcat = spec_income.objects.get(id = id)
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
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def specincdelete(request, id):
    try:
        newcat = spec_income.objects.get(id = id)
        newcat.delete() 
    except:
        return HttpResponse('{"status": "Ошибка удаления категории"}', content_type="application/json", status = 400)

    queryset = spec_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def classificationinclist(request):
    queryset = classification_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = classificatinIncSerializer(paginated_queryset, many = True)
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

    category = data['category']
    classs = data['class']
    podclass = data['podclass']
    spec = data['spec']

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
        return HttpResponse('{"status": "Ошибка добавления классификации по поступлениям. Неверные данные"}', content_type="application/json", status = 400) 

    queryset = classification_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def classificationincedit(request):

    datastr = request.body
    data = json.loads(datastr)

    id = data['id']
    category = data['category']
    classs = data['class']
    podclass = data['podclass']
    spec = data['spec']

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
        return HttpResponse('{"status": "Ошибка изменения классификации по поступлениям. Неверные данные"}', content_type="application/json", status = 400) 

    queryset = classification_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def classificationincdelete(request, id):
    try:
        newcat = classification_income.objects.get(id = id)
        newcat.delete() 
    except:
        return HttpResponse('{"status": "Ошибка удаления классификации поступления"}', content_type="application/json", status = 400)

    queryset = classification_income.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def typeincdoclist(request):
    queryset = type_izm_doc.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)




# ****************************************************************
# ****************Сервисы справочников расхода********************
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def funcgrouplist(request):
    queryset = funcgroup.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def funcpodgrouplist(request):
    queryset = funcpodgroup.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def abplist(request):
    queryset = abp.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def programlist(request):
    queryset = program.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def podprogramlist(request):
    queryset = podprogram.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fkrlist(request):
    queryset = fkr.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def specexplist(request):
    queryset = spec_exp.objects.all()
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = shareSerializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)













