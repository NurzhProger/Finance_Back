from django.http import HttpResponse
from rest_framework import pagination, response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json, io
import base64
from datetime import datetime
from django.db import connection, transaction
from .models import *
from .serializer import *
# Общий модуль импортируем
from .shareModuleInc import object_svod_get, getqsetlist
from PyPDF2 import PdfReader


class CustomPagination(pagination.LimitOffsetPagination):
    default_limit = 25  # Количество объектов на странице по умолчанию
    max_limit = 50     # Максимальное количество объектов на странице



# ****************************************************************
# ***Сервисы утвержденного плана финансирования по поступлениям***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvinclist(request):
    queryset = getqsetlist(utv_inc, request.user, 'nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_inc_Serializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvincitem(request, id):

    if (id == 0):
        try:
            org = profile.objects.get(_user_id=request.user.pk)._organization
        except:
            response_data = {
                "status": "Не указана текущая организация в профиле пользователя"}
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

        resp = {
            "doc": {
                "id": 0,
                "_organization": {
                    "id": org.id,
                    "name_rus": org.name_rus,
                    "name_kaz": org.name_kaz
                },
                "_date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "_type_izm_doc": {
                    "id": 0,
                    "name_kaz": "",
                    "name_rus": ""
                },
                "nom": ""
            },
            "tbl1": []
        }
        return response.Response(resp)

    # Документ сам (шапка документа)
    queryset_doc = utv_inc.objects.get(id=id)
    serialdoc = utv_inc_Serializer(queryset_doc)

    # табличная часть
    queryset_tbl1 = utv_inc_tbl1.objects.filter(_utv_inc_id=queryset_doc.id)
    serial_tbl1 = utv_inc_tbl1_Serializer(queryset_tbl1, many=True)

    # Возвращаем шапку и табличную часть в одном объекте
    resp = {'doc': serialdoc.data,
            'tbl1': serial_tbl1.data}
    return response.Response(resp)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def utvincsave(request):
    datastr = request.body
    data = json.loads(datastr)
    doc_req = data['doc']
    tbl1_req = data['tbl1']

    date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
    org = organization.objects.get(id=doc_req['_organization']['id'])

    try:
        with transaction.atomic():
            if doc_req['id'] == None or doc_req['id'] == 0:
                year = date_object.year
                doc_cnt = utv_inc.objects.filter(
                    _date__year=year, _organization_id=org.id).count()
                itemdoc = utv_inc()
                itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            else:
                itemdoc = utv_inc.objects.get(id=doc_req['id'])

            itemdoc._organization_id = org.id
            itemdoc._budjet_id = org._budjet.id
            itemdoc._date = date_object
            itemdoc.deleted = False
            itemdoc.save()

            # Очищаем предыдущие записи табличной части
            del_pay_obl = f"""DELETE FROM docs_utv_inc_tbl1 WHERE _utv_inc_id = {itemdoc.id};
                              DELETE FROM docs_reg_inc WHERE _utv_inc_id = {itemdoc.id};"""
            with connection.cursor() as cursor:
                cursor.execute(del_pay_obl)

            rows_save_tbl = []
            rows_save_reg = []

            for itemtbl1 in tbl1_req:
                newitemtbl1 = utv_inc_tbl1()
                newitemtbl1._utv_inc_id = itemdoc.id
                newitemtbl1._classification_id = itemtbl1['_classification']['id']
                newitemtbl1._organization_id = doc_req['_organization']['id']
                newitemtbl1._date = date_object.date()
                god = 0
                for ind in range(1, 13):
                    sm = itemtbl1['sm'+str(ind)] if not itemtbl1['sm' +
                                                                 str(ind)] == None else 0
                    god += sm
                    setattr(newitemtbl1, 'sm' + str(ind), sm)
                newitemtbl1.god = god
                newitemtbl1.deleted = False
                rows_save_tbl.append(newitemtbl1)

                reg_new_rec = reg_inc()
                reg_new_rec._utv_inc_id = itemdoc.id
                reg_new_rec._classification_id = itemtbl1['_classification']['id']
                reg_new_rec._organization_id = org.id
                reg_new_rec._date = date_object
                reg_new_rec._budjet_id = itemdoc._budjet_id
                god = 0
                for ind in range(1, 13):
                    sm = itemtbl1['sm'+str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    god += sm
                    setattr(reg_new_rec, 'sm' + str(ind), sm)
                reg_new_rec.god = god
                # reg_new_rec.save()
                # Помещаем в массив строки для дальнейшей записи за одно обращение
                rows_save_reg.append(reg_new_rec)

            utv_inc_tbl1.objects.bulk_create(rows_save_tbl)
            reg_inc.objects.bulk_create(rows_save_reg)
            return response.Response({"status":"Документ успешно записан", "id_doc":itemdoc.id, "nom":itemdoc.nom})

    except Exception as e:
        return HttpResponse('{"status": "Ошибка сохранения документа"}', content_type="application/json", status=400)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def utvincdelete(request):
    req = json.loads(request.body)
    docs = req['mass_doc_id']
    shift = req['shift']
    is_admin = (request.user.groups.filter(name='fulldata').count()>0)
    if shift and is_admin:
        try:
            for id in docs:
                with transaction.atomic():
                    utv_inc.objects.get(id=id).delete()
                    # табличная часть
                    utv_inc_tbl1.objects.filter(_utv_inc_id=id).delete()
                    # таблица проводок
                    reg_inc.objects.filter(_utv_inc_id = id).delete()
        except:
            a = 1
    else:
        try:
            for id in docs:
                with transaction.atomic():
                    docobj = utv_inc.objects.get(id=id)
                    docobj.deleted = True
                    docobj.save()

                    # табличная часть
                    utv_inc_tbl1.objects.filter(_utv_inc_id=id).update(deleted = True)
                    # таблица проводок
                    reg_inc.objects.filter(_utv_inc_id = id).delete()
        except:
            a = 1

    return response.Response({"status":"успешно"})




# ****************************************************************
# *****Сервисы изменения плана финансирования по поступлениям*****
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izminclist(request):
    queryset = getqsetlist(izm_inc, request.user, 'nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_inc_Serializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmincitem(request, id):

    queryset = type_izm_doc.objects.all()
    serialtype = typedocSerializer(queryset, many=True)

    if (id == 0):
        try:
            org = profile.objects.get(_user_id=request.user.pk)._organization
        except:
            response_data = {
                "status": "Не указана текущая организация в профиле пользователя"}
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

        resp = {
            "doc": {
                "id": 0,
                "_organization": {
                    "id": org.id,
                    "name_rus": org.name_rus,
                    "name_kaz": org.name_kaz
                },
                "_date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "_type_izm_doc": {
                    "id": 0,
                    "name_kaz": "",
                    "name_rus": ""
                },
                "nom": ""
            },
            "tbl1": [],
            'typesdoc': serialtype.data
        }
        return response.Response(resp)

    # Документ сам (шапка документа)
    queryset_doc = izm_inc.objects.get(id=id)
    serialdoc = izm_inc_Serializer(queryset_doc)

    queryset_tbl1 = izm_inc_tbl1.objects.filter(
        _izm_inc_id=queryset_doc.id).order_by('_classification')
    serialtbl1 = izm_inc_tbl1_Serializer(queryset_tbl1, many=True)

    resp = {
        'doc': serialdoc.data,
        'tbl1': serialtbl1.data,
        'typesdoc': serialtype.data
    }
    tbl1res = json.dumps(resp)
    return HttpResponse(tbl1res, content_type="application/json", status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def izmincsave(request):
    datastr = request.body
    data = json.loads(datastr)
    doc_req = data['doc']
    tbl1_req = data['tbl1']
    org_id = doc_req['_organization']['id']
    doc_id = doc_req['id']

    try:
        with transaction.atomic():
            # Запис шапки документа изменения по поступлениям
            date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
            org = organization.objects.get(id=org_id)
            bjt_id = org._budjet.id

            # Если ИД=0, то создаем новый документ поступления
            if doc_id == 0:
                itemdoc = izm_inc()
                year = date_object.year
                doc_cnt = izm_inc.objects.filter(_date__year=year).count()
                itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            # Иначе получаем уже имеющиеся документ
            else:
                itemdoc = izm_inc.objects.get(id=doc_id)

            itemdoc._organization_id = org.id
            itemdoc._type_izm_doc_id = doc_req['_type_izm_doc']['id']
            itemdoc._budjet_id = org._budjet.id
            itemdoc._date = date_object
            itemdoc.deleted = False
            # Непосредственно сохранение документа
            itemdoc.save()

            # Очищаем предыдущие записи табличной части
            del_pay_obl = f"""DELETE FROM docs_izm_inc_tbl1 WHERE _izm_inc_id = {itemdoc.id};
                              DELETE FROM docs_reg_inc WHERE _izm_inc_id = {itemdoc.id};"""
            with connection.cursor() as cursor:
                cursor.execute(del_pay_obl)

            rows_save = []
            rows_save_reg = []
            # Запись табличной части документа изменения по поступлениям
            for itemtbl1 in tbl1_req:
                newitemtbl1 = izm_inc_tbl1()
                newitemtbl1._izm_inc_id = itemdoc.id
                newitemtbl1._classification_id = itemtbl1['_classification']['id']
                newitemtbl1._organization_id = org_id
                newitemtbl1._date = date_object

                for ind in range(1, 13):
                    utv = itemtbl1['utv' + str(ind)] if not itemtbl1['utv' + str(ind)] == None else 0
                    sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    itog = itemtbl1['itog' + str(ind)] if not itemtbl1['itog' + str(ind)] == None else 0

                    # Проверка изменения сумм на предыдущие месяцы. Если изменения есть, то отменяем транзакцию и возвращаем ошибку.
                    if ind < date_object.month:
                        if not (sm == 0):
                            transaction.rollback("Ошибка, нельзя менять предыдущие месяцы!")
                            # return HttpResponse('{"status": "Ошибка, нельзя менять предыдущие месяцы!"}', content_type="application/json", status=400)
                    # Проверка изменения сумм на последующие месяцы. Сумма не должна превышать остатка на текущий месяц.
                    if ind > date_object.month:
                        if (utv + sm) < 0:
                            transaction.rollback("Ошибка, Сумма больше остатка!")
                            # return HttpResponse('{"status": "Ошибка, Сумма больше остатка!!"}', content_type="application/json", status=400)

                    # Если ошибок нет, то заполняем значения своиств за 12 месяцев
                    setattr(newitemtbl1, 'utv' + str(ind), utv)
                    setattr(newitemtbl1, 'sm' + str(ind), sm)
                    setattr(newitemtbl1, 'itog' + str(ind), itog)
                # Помещаем в массив строки для дальнейшей записи за одно обращение
                rows_save.append(newitemtbl1)

                reg_new_rec = reg_inc()
                reg_new_rec._izm_inc_id = itemdoc.id
                reg_new_rec._classification_id = itemtbl1['_classification']['id']
                reg_new_rec._organization_id = org_id
                reg_new_rec._date = date_object
                reg_new_rec._budjet_id = bjt_id
                god = 0
                for ind in range(1, 13):
                    sm = itemtbl1['sm'+str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    god += sm
                    setattr(reg_new_rec, 'sm' + str(ind), sm)
                reg_new_rec.god = god
                # Помещаем в массив строки для дальнейшей записи за одно обращение
                rows_save_reg.append(reg_new_rec)

            izm_inc_tbl1.objects.bulk_create(rows_save)
            reg_inc.objects.bulk_create(rows_save_reg)

            list_clasif = []
            list_clasif.append(0)
            list_clasif.append(0)
            for itm in tbl1_req:
                list_clasif.append(itm['_classification']['id'])

            date = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
            date_start = datetime.strptime(str(date.year) + "-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
            dateend = date

            query = f"""with reg as (SELECT _classification_id, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12
                                    FROM public.docs_reg_inc
                                    WHERE _classification_id in {tuple(list_clasif)} and  _organization_id = {org_id} and _date>='{date_start}' and _date <= '{dateend}'
                                    group by _classification_id),        
                            classname as (SELECT * FROM public.dirs_classification_income
                                    WHERE id in (select _classification_id from reg))
                            SELECT classname.id as _classification, classname.code as classification_code, classname.name_rus as classification_name,
                                COALESCE(sum(sm1),0) as sm1,
                                COALESCE(sum(sm1) + sum(sm2),0) as sm2,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3),0) as sm3,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4),0) as sm4,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5),0) as sm5,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5) + sum(sm6),0) as sm6,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5) + sum(sm6) + sum(sm7),0) as sm7,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5) + sum(sm6) + sum(sm7) + sum(sm8),0) as sm8,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5) + sum(sm6) + sum(sm7) + sum(sm8) + sum(sm9),0) as sm9,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5) + sum(sm6) + sum(sm7) + sum(sm8) + sum(sm9) + sum(sm10),0) as sm10,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5) + sum(sm6) + sum(sm7) + sum(sm8) + sum(sm9) + sum(sm10) + sum(sm11),0) as sm11,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5) + sum(sm6) + sum(sm7) + sum(sm8) + sum(sm9) + sum(sm10) + sum(sm11) + sum(sm12),0) as sm12
                            FROM reg
                            LEFT JOIN classname ON reg._classification_id = classname.id
                            GROUP BY _classification, classification_code, classification_name"""

            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row))
                          for row in cursor.fetchall()]

            err = False
            for res in result:
                for count in range(1, 13):
                    if (res['sm'+str(count)]) < 0:
                        err = True

            if (err):
                transaction.rollback("Ошибка сохранения документа. Проверьте введенные суммы!")

            resjson = {'status':'Документ успешно сохранен №' + str(itemdoc.nom),
                        'id_doc':itemdoc.id,
                        'nom':itemdoc.nom}
            return response.Response(resjson)
    except Exception as e:
        response_data = {
            "status": e.args[0]
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def izmincdelete(request):
    req = json.loads(request.body)
    docs = req['mass_doc_id']
    shift = req['shift']
    is_admin = (request.user.groups.filter(name='fulldata').count()>0)
    if shift and is_admin:
        for id in docs:
            try:
                with transaction.atomic():
                    izm_inc_tbl1.objects.filter(_izm_inc_id=id).delete()
                    reg_inc.objects.filter(_izm_inc_id=id).delete()
                    docobj = izm_inc.objects.get(id=id)
                    docobj.delete()
            except: a = 1
    else:
        for id in docs:
            try:
                izm_inc.objects.filter(id=id).update(deleted = True)
                izm_inc_tbl1.objects.filter(_izm_inc_id=id).update(deleted = True)
                reg_inc.objects.filter(_izm_inc_id=id).delete()
            except: a = 1
    return response.Response({"status":"ok"})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def incgetplanbyclassif(request):
    _organization = request.GET.get("_organization")
    _classification = request.GET.get("_classification")
    strdate = request.GET.get("date")

    if _organization == None:
        return HttpResponse('{"status": "Ошибка получения данных"}', content_type="application/json", status=400)

    date = None
    if not strdate == None:
        date = datetime.strptime(strdate, "%d.%m.%Y %H:%M:%S")
    start_of_year = date.replace(month=1, day=1, hour=0, minute=0, second=0)


    query = f"""with reg as (SELECT _classification_id, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12
                                    FROM public.docs_reg_inc
                                    WHERE _classification_id = {_classification} and  _organization_id = {_organization} and _date>='{start_of_year}' and _date <= '{date}'
                                    group by _classification_id),        
                            classname as (SELECT * FROM public.dirs_classification_income
                                    WHERE id ={_classification})
                            SELECT classname.id as _classification, max(classname.code) as classification_code, max(classname.name_rus) as classification_name,
                                COALESCE(sum(sm1), 0) as sm1,
                                COALESCE(sum(sm2),0) as sm2,
                                COALESCE(sum(sm3),0) as sm3,
                                COALESCE(sum(sm4),0) as sm4,
                                COALESCE(sum(sm5),0) as sm5,
                                COALESCE(sum(sm6),0) as sm6,
                                COALESCE(sum(sm7),0) as sm7,
                                COALESCE(sum(sm8),0) as sm8,
                                COALESCE(sum(sm9),0) as sm9,
                                COALESCE(sum(sm10),0) as sm10,
                                COALESCE(sum(sm11),0) as sm11,
                                COALESCE(sum(sm12),0) as sm12,
                                COALESCE(sum(sm1) + sum(sm2) + sum(sm3) + sum(sm4) + sum(sm5) + sum(sm6) + sum(sm7) + sum(sm8) + sum(sm9) + sum(sm10) + sum(sm11) + sum(sm12),0) as god
                            FROM reg
                            RIGHT JOIN classname ON reg._classification_id = classname.id
                            GROUP BY _classification"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row))
                for row in cursor.fetchall()]

    if len(data) > 0:
        res = data[0]
        obj = {
            "id": 0,
            "_classification": {
                "id": res['_classification'],
                "name_kaz": res['classification_name'],
                "name_rus": res['classification_name'],
                "code": res['classification_code']
            },
            "_date": "", 
            "deleted": False, 
            "utvgod": 0, 
            "god": res['god'], 
            "itoggod": 0
        }

        for ind in range(1, 13):
            obj["utv" + str(ind)] = res["sm" + str(ind)]
            obj["sm" + str(ind)] = 0
            obj["itog" + str(ind)] = 0
    else:
        obj = {
            "id": 0,
            "_classification": {
                "id": 0,
                "name_kaz": '',
                "name_rus": '',
                "code": ''
            },
            "_date": "", 
            "deleted": False, 
            "utvgod": 0, 
            "god": 0, 
            "itoggod": 0
        }

    return HttpResponse(json.dumps(obj), content_type="application/json")




# ****************************************************************
# ***Сервисы утвержденного плана финансирования по расходам***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvexplist(request):
    queryset = getqsetlist(utv_exp, request.user, 'nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_exp_Serializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvexpitem(request, id):

    if (id == 0):
        try:
            org = profile.objects.get(_user_id=request.user.pk)._organization
        except:
            response_data = {
                "status": "Не указана текущая организация в профиле пользователя"}
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

        resp = {
            "doc": {
                "id": 0,
                "_organization": {
                    "id": org.id,
                    "name_rus": org.name_rus,
                    "name_kaz": org.name_kaz
                },
                "_date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "_type_izm_doc": {
                    "id": 0,
                    "name_kaz": "",
                    "name_rus": ""
                },
                "nom": ""
            },
            "payments": [],
            "obligats": []
        }
        return response.Response(resp)

    # Документ сам (шапка документа)
    queryset_doc = utv_exp.objects.get(id=id)
    serialdoc = utv_exp_Serializer(queryset_doc)


    # Получаем запросом таблицу по платежам
    query = f"""with tbl as (SELECT * FROM public.docs_utv_exp_pay where _utv_exp_id = {id}),        
                     fkr as (SELECT * FROM public.dirs_fkr WHERE id in (select _fkr_id from tbl)),
                     spec as (SELECT * FROM public.dirs_spec_exp WHERE id in (select _spec_id from tbl))
                SELECT tbl.id, fkr.id as fkr_id, fkr.code as fkr_code, fkr.name_rus as fkr_name, spec.id as spec_id, spec.code as spec_code, spec.name_rus as spec_name,
                    sm1,sm2,sm3,sm4,sm5,sm6,sm7,sm8,sm9,sm10,sm11,sm12, false as deleted
                FROM tbl
                left JOIN fkr
                ON tbl._fkr_id = fkr.id
                left JOIN spec
                ON tbl._spec_id = spec.id
                ORDER BY tbl.id"""
    data = []
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row))
                for row in cursor.fetchall()]

    payment = []
    for item in data:
        jsonobj = {
            "id": item['id'],
            "_fkr": {
                "id": item['fkr_id'],
                "code": item['fkr_code'],
                "name_rus": item['fkr_name']
            },
            "_spec": {
                "id": item['spec_id'],
                "code": item['spec_code'],
                "name_rus": item['spec_name']
            },
            "sm1":item['sm1'],
            "sm2":item['sm2'],
            "sm3":item['sm3'],
            "sm4":item['sm4'],
            "sm5":item['sm5'],
            "sm6":item['sm6'],
            "sm7":item['sm7'],
            "sm8":item['sm8'],
            "sm9":item['sm9'],
            "sm10":item['sm10'],
            "sm11":item['sm11'],
            "sm12":item['sm12'],
        }
        payment.append(jsonobj)


    # Получаем запросом таблицу по обязательствам
    query = f"""with tbl as (SELECT * FROM public.docs_utv_exp_obl where _utv_exp_id = {id}),        
                     fkr as (SELECT * FROM public.dirs_fkr WHERE id in (select _fkr_id from tbl)),
                     spec as (SELECT * FROM public.dirs_spec_exp WHERE id in (select _spec_id from tbl))
                SELECT tbl.id, fkr.id as fkr_id, fkr.code as fkr_code, fkr.name_rus as fkr_name, spec.id as spec_id, spec.code as spec_code, spec.name_rus as spec_name,
                    sm1,sm2,sm3,sm4,sm5,sm6,sm7,sm8,sm9,sm10,sm11,sm12, false as deleted
                FROM tbl
                left JOIN fkr
                ON tbl._fkr_id = fkr.id
                left JOIN spec
                ON tbl._spec_id = spec.id
                ORDER BY tbl.id"""
    data = []
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row))
                for row in cursor.fetchall()]

    obligats = []
    for item in data:
        jsonobj = {
            "id": item['id'],
            "_fkr": {
                "id": item['fkr_id'],
                "code": item['fkr_code'],
                "name_rus": item['fkr_name']
            },
            "_spec": {
                "id": item['spec_id'],
                "code": item['spec_code'],
                "name_rus": item['spec_name']
            },
            "sm1":item['sm1'],
            "sm2":item['sm2'],
            "sm3":item['sm3'],
            "sm4":item['sm4'],
            "sm5":item['sm5'],
            "sm6":item['sm6'],
            "sm7":item['sm7'],
            "sm8":item['sm8'],
            "sm9":item['sm9'],
            "sm10":item['sm10'],
            "sm11":item['sm11'],
            "sm12":item['sm12'],
        }
        obligats.append(jsonobj)


    # Возвращаем шапку и табличную часть в одном объекте
    resp = {'doc': serialdoc.data,
            'payments': payment,
            'obligats': obligats,
            }
    return response.Response(resp)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def utvexpsave(request):
    datastr = request.body
    data = json.loads(datastr)
    doc_req = data['doc']
    payments = data['payments']
    obligs = data['obligats']

    for itemtbl1 in payments:
        for ind in range(1, 13):
            sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
            if sm < 0:
                return HttpResponse('{"status": "Сумма в утвержденном плане (платежи) не должна быть меньше 0"}', content_type="application/json", status=400)

    for itemtbl1 in obligs:
        for ind in range(1, 13):
            sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
            if sm < 0:
                return HttpResponse('{"status": "Сумма в утвержденном плане (обязательства) не должна быть меньше 0"}', content_type="application/json", status=400)

    try:
        with transaction.atomic():
            # Начало записи шапки документа--------------------------------------
            doc_id = doc_req['id']
            org = organization.objects.get(id=doc_req['_organization']['id'])
            budjet_id = org._budjet.id
            date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')

            if doc_req['id'] == 0:
                year = date_object.year
                doc_list = utv_exp.objects.filter(_date__year=year, _organization=org.id)
                correct = True
                for itemdoc in doc_list:
                    if not itemdoc.deleted:
                        correct = False

                if not correct:
                    transaction.rollback('Утвержденный план на этот год уже имеется. Удалите предыдущий документ!')

                itemdoc = utv_exp()
                itemdoc.nom = str(doc_list.count() + 1) + '-' + org.bin
            else:
                itemdoc = utv_exp.objects.get(id=doc_id)

            itemdoc._organization_id = org.id
            itemdoc._budjet_id = budjet_id
            itemdoc._date = date_object
            itemdoc.deleted = False
            itemdoc.save()
            # -----------конец записи шапки документа-----------------------------


            # Начало записи табличных частей документа
            # Очищаем предыдущие записи табличной части
            del_pay_obl = f"""DELETE FROM docs_utv_exp_pay WHERE _utv_exp_id = {itemdoc.id};
                              DELETE FROM docs_utv_exp_obl WHERE _utv_exp_id = {itemdoc.id};
                              DELETE FROM docs_reg_exp_pay WHERE _utv_exp_id = {itemdoc.id};
                              DELETE FROM docs_reg_exp_obl WHERE _utv_exp_id = {itemdoc.id};
                            """
            with connection.cursor() as cursor:
                cursor.execute(del_pay_obl)

            izm_exp_pay_list = []
            izm_exp_obl_list = []
            reg_exp_pay_list = []
            reg_exp_obl_list = []

            for itemtbl1 in payments:
                if (itemtbl1['_fkr']['id'] == 0):
                    continue

                newitemtbl1 = utv_exp_pay()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                # newitemtbl1.god = itemtbl1['god']
                for ind in range(1, 13):
                    sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    setattr(newitemtbl1, 'sm' + str(ind), sm)
                izm_exp_pay_list.append(newitemtbl1)

                newregrec = reg_exp_pay()
                newregrec._utv_exp_id = itemdoc.id
                newregrec._fkr_id = itemtbl1['_fkr']['id']
                newregrec._spec_id = itemtbl1['_spec']['id']
                newregrec._organization_id = org.id
                newregrec._budjet_id = org._budjet.id
                newregrec._date = date_object
                # newregrec.god = itemtbl1['god']
                god = 0
                for ind in range(1, 13):
                    sm = itemtbl1['sm' +
                                  str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    god += sm
                    setattr(newregrec, 'sm' + str(ind), sm)
                newregrec.god = god
                reg_exp_pay_list.append(newregrec)


            for itemtbl1 in obligs:
                if (itemtbl1['_fkr']['id'] == 0):
                    continue
                newitemtbl1 = utv_exp_obl()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                # newitemtbl1.god = itemtbl1['god']
                for ind in range(1, 13):
                    sm = itemtbl1['sm' +
                                  str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    setattr(newitemtbl1, 'sm' + str(ind), sm)
                izm_exp_obl_list.append(newitemtbl1)

                newregrec = reg_exp_obl()
                newregrec._utv_exp_id = itemdoc.id
                newregrec._fkr_id = itemtbl1['_fkr']['id']
                newregrec._spec_id = itemtbl1['_spec']['id']
                newregrec._organization_id = org.id
                newregrec._budjet_id = org._budjet.id
                newregrec._date = date_object
                god = 0
                for ind in range(1, 13):
                    sm = itemtbl1['sm' +
                                  str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    god += sm
                    setattr(newregrec, 'sm' + str(ind), sm)
                newregrec.god = god
                reg_exp_obl_list.append(newregrec)

            utv_exp_pay.objects.bulk_create(izm_exp_pay_list)
            utv_exp_obl.objects.bulk_create(izm_exp_obl_list)

            reg_exp_pay.objects.bulk_create(reg_exp_pay_list)
            reg_exp_obl.objects.bulk_create(reg_exp_obl_list)

            query = f"""with obl as (SELECT _fkr_id, _spec_id, sum(god) as god_obl
                                    FROM public.docs_reg_exp_obl
                                    WHERE _utv_exp_id = {itemdoc.id} and _organization_id={org.id}
                                    GROUP BY _fkr_id, _spec_id),
                            pay as (SELECT _fkr_id, _spec_id, sum(god) as god_pay 
                                    FROM public.docs_reg_exp_pay
                                    WHERE _utv_exp_id = {itemdoc.id} and _organization_id={org.id}
                                    GROUP BY _fkr_id, _spec_id)
                            
                            select obl.god_obl, pay.god_pay from obl
                            join pay 
                            on obl._fkr_id = pay._fkr_id and obl._spec_id = pay._spec_id
                            where obl.god_obl <> pay.god_pay"""
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row))
                          for row in cursor.fetchall()]

            if len(result) > 0:
                transaction.rollback("Суммы платежей и обязательства не совпадают")

            return HttpResponse('{"status": "Успешно записан документ"}', content_type="application/json")

    except Exception as e:
        response_data = {
            "status": e.args[0]
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def utvexpdelete(request, id):

    try:
        with transaction.atomic():
            docobj = utv_exp.objects.get(id=id)
            znach = docobj.deleted
            docobj.deleted = not znach
            docobj.save()

            utv_exp_pay.objects.filter(_utv_exp_id=docobj.id).update(deleted = not znach)
            utv_exp_obl.objects.filter(_utv_exp_id=docobj.id).update(deleted = not znach)


            del_pay_obl = f"""DELETE FROM docs_reg_exp_pay WHERE _utv_exp_id = {id};
                              DELETE FROM docs_reg_exp_obl WHERE _utv_exp_id = {id};"""
            with connection.cursor() as cursor:
                cursor.execute(del_pay_obl)
    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status=400)
    return HttpResponse('{"status": "Успешно удален"}', content_type="application/json", status=200)



# ****************************************************************
# ***Сервисы изменения плана***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmexplist(request):
    queryset = getqsetlist(izm_exp, request.user, 'nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_exp_serial(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmexpitem(request, id_doc):
    try:
        org = profile.objects.get(_user_id=request.user.pk)._organization
    except:
        response_data = {
            "status": "Не указана текущая организация в профиле пользователя"}
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

    queryset = type_izm_doc.objects.all()
    serialtype = typedocSerializer(queryset, many=True)
    jsondata = {
        "doc": {
            "id": 0,
            "nom": "",
            "_date": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            "_organization": {
                "id": org.id,
                "name_rus": org.name_rus
            },
            "_type_izm_doc": {
                "id": 0,
                "name_kaz": "",
                            "name_rus": ""
            }
        },
        "payments": [],
        "obligats": [],
        'typesdoc': serialtype.data
    }

    if (id_doc == 0):
        return response.Response(jsondata)

    querydoc = f"""with doc as (SELECT * FROM public.docs_izm_exp
                                WHERE id = {id_doc}),
                        org as (select id, bin, name_rus from public.dirs_organization
                                where id in (select _organization_id from doc)),
                        type_izm as (select id, name_rus from public.dirs_type_izm_doc
                                where id in (select 	_type_IZM_DOC_ID from doc))
                                
                    select doc.id, doc.nom, doc._date, type_izm.id as _type_izm_doc_id, type_izm.name_rus as _type_izm_doc_name, 
                            org.id as _organization_id, org.name_rus as _organization_name
                    from type_izm, org, doc"""

    querypay = f"""with pay as (SELECT * FROM public.docs_izm_exp_pay
                                WHERE _izm_exp_id = {id_doc}),
                        fkr as (select id as _fkr_id, code as _fkr_code, name_rus as _fkr_name from public.dirs_fkr
                                WHERE id in (select _fkr_id from pay)),
                        spec as (select id as _spec_id, code as _spec_code, name_rus as _spec_name from public.dirs_spec_exp
                                WHERE id in (select _spec_id from pay))
                        
                    select  fkr.*, spec.*, pay.* from pay
                    left join fkr
                    on pay._fkr_id = fkr._fkr_id
                    left join spec
                    on pay._spec_id = spec._spec_id
                    order by fkr._fkr_code, spec._spec_code"""

    queryobl = f"""with pay as (SELECT * FROM public.docs_izm_exp_obl
                                WHERE _izm_exp_id = {id_doc}),
                        fkr as (select id as _fkr_id, code as _fkr_code, name_rus as _fkr_name from public.dirs_fkr
                                WHERE id in (select _fkr_id from pay)),
                        spec as (select id as _spec_id, code as _spec_code, name_rus as _spec_name from public.dirs_spec_exp
                                WHERE id in (select _spec_id from pay))
                        
                    select  fkr.*, spec.*, pay.* from pay
                    left join fkr
                    on pay._fkr_id = fkr._fkr_id
                    left join spec
                    on pay._spec_id = spec._spec_id
                    order by fkr._fkr_code, spec._spec_code"""

    with connection.cursor() as cursor:
        cursor.execute(querydoc)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    with connection.cursor() as cursor:
        cursor.execute(querypay)
        columns = [col[0] for col in cursor.description]
        resultpay = [dict(zip(columns, row))
                     for row in cursor.fetchall()]

    with connection.cursor() as cursor:
        cursor.execute(queryobl)
        columns = [col[0] for col in cursor.description]
        resultobl = [dict(zip(columns, row))
                     for row in cursor.fetchall()]

    if len(result) == 0:
        response_data = {
            "status": "Ошибка, не найден выбранный документ в базе"}
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

    jsondata['doc']['id'] = result[0]['id']
    jsondata['doc']['_date'] = result[0]['_date'].strftime("%d.%m.%Y %H:%M:%S")
    jsondata['doc']['nom'] = result[0]['nom']
    jsondata['doc']['_organization']['id'] = result[0]['_organization_id']
    jsondata['doc']['_organization']['name_rus'] = result[0]['_organization_name']
    jsondata['doc']['_type_izm_doc']['id'] = result[0]['_type_izm_doc_id']
    jsondata['doc']['_type_izm_doc']['name_rus'] = result[0]['_type_izm_doc_name']
    jsondata['payments'] = resultpay
    jsondata['obligats'] = resultobl
    return response.Response(jsondata)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def izmexpsave(request):
    datastr = request.body
    data = json.loads(datastr)
    doc_req = data['doc']
    payments = data['payments']
    obligs = data['obligats']

    if not len(payments)==len(obligs):
        response_data = {"status": "Количество строк в платежах и в обязательствам разные."}
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

    try:
        org = organization.objects.get(id=doc_req['_organization']['id'])
        budjet_id = org._budjet.id
        date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
        year = date_object.year
        month = date_object.month

        # Начало транзации записи документа
        with transaction.atomic():
            if doc_req['id'] == 0:
                doc_cnt = izm_exp.objects.filter(
                    _date__year=year, _organization=org.id).count()
                itemdoc = izm_exp()
                itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            else:
                itemdoc = izm_exp.objects.get(id=doc_req['id'])
            itemdoc._organization_id = org.id
            itemdoc._budjet_id = budjet_id
            itemdoc._date = date_object
            itemdoc.deleted = False
            if doc_req['_type_izm_doc']['id'] == 0:
                itemdoc._type_izm_doc_id = 1
            else:
                itemdoc._type_izm_doc_id = doc_req['_type_izm_doc']['id']
            itemdoc.save()

            # Очищаем предыдущие записи табличной части
            del_records = f"""DELETE FROM docs_izm_exp_pay WHERE _izm_exp_id = {itemdoc.id};
                              DELETE FROM docs_izm_exp_obl WHERE _izm_exp_id = {itemdoc.id};
                              DELETE FROM docs_reg_exp_pay WHERE _izm_exp_id = {itemdoc.id};
                              DELETE FROM docs_reg_exp_obl WHERE _izm_exp_id = {itemdoc.id};
                              """
            with connection.cursor() as cursor:
                cursor.execute(del_records)

            izm_exp_pay_list = []
            izm_exp_obl_list = []
            reg_exp_pay_list = []
            reg_exp_obl_list = []
            for itemtbl1 in payments:
                newitemtbl1 = izm_exp_pay()
                newitemtbl1._izm_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr_id']
                newitemtbl1._spec_id = itemtbl1['_spec_id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                for ind in range(12, 0, -1):
                    utv = itemtbl1['utv' + str(ind)] if not itemtbl1['utv' + str(ind)] == None else 0
                    sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    itog = itemtbl1['itog' + str(ind)] if not itemtbl1['itog' + str(ind)] == None else 0

                    # Проверка редактирования предыдущих месяцев
                    if (month > ind) and not (sm == 0):
                        transaction.rollback("Нельзя редактировать предыдущие месяцы")

                    if (month < ind) and ((utv + sm) < 0):
                        transaction.set_rollback("Нельзя в будущих месяцах указывать сумму больше остатка!")

                    setattr(newitemtbl1, 'utv' + str(ind), utv)
                    setattr(newitemtbl1, 'sm' + str(ind), sm)
                    setattr(newitemtbl1, 'itog' + str(ind), itog)
                izm_exp_pay_list.append(newitemtbl1)

                newregrec = reg_exp_pay()
                newregrec._izm_exp_id = itemdoc.id
                newregrec._fkr_id = itemtbl1['_fkr_id']
                newregrec._spec_id = itemtbl1['_spec_id']
                newregrec._organization_id = org.id
                newregrec._date = date_object
                god = 0
                for ind in range(12, 0, -1):
                    utv = itemtbl1['utv' + str(ind)] if not itemtbl1['utv' + str(ind)] == None else 0
                    sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    setattr(newregrec, 'sm' + str(ind), sm)
                    if (month == ind) and ((utv + sm) < 0):
                        ost = -sm
                        j = ind
                        while ost > 0 and j > 0:
                            utv_new = itemtbl1['utv' +
                                               str(j)] if not itemtbl1['utv' + str(j)] == None else 0
                            sum = min(utv_new, ost)
                            setattr(newregrec, 'sm' + str(j), -sum)
                            god += (-sum)
                            ost -= sum
                            j -= 1

                        if ost > 0:
                            transaction.rollback("Не хватает сумм в платежах. Проверьте суммы.")
                        break
                newregrec.god = god
                reg_exp_pay_list.append(newregrec)

            izm_exp_pay.objects.bulk_create(izm_exp_pay_list)
            reg_exp_pay.objects.bulk_create(reg_exp_pay_list)

            for itemtbl2 in obligs:
                newitemtbl2 = izm_exp_obl()
                newitemtbl2._izm_exp_id = itemdoc.id
                newitemtbl2._fkr_id = itemtbl2['_fkr_id']
                newitemtbl2._spec_id = itemtbl2['_spec_id']
                newitemtbl2._organization_id = org.id
                newitemtbl2._date = date_object
                for ind in range(1, 13):
                    utv = itemtbl2['utv' + str(ind)] if not itemtbl2['utv' + str(ind)] == None else 0
                    setattr(newitemtbl2, 'utv' + str(ind), utv)
                for ind in range(1, 13):
                    sm = itemtbl2['sm' + str(ind)] if not itemtbl2['sm' + str(ind)] == None else 0
                    setattr(newitemtbl2, 'sm' + str(ind), sm)
                for ind in range(1, 13):
                    itog = itemtbl2['itog' + str(ind)] if not itemtbl2['itog' + str(ind)] == None else 0
                    setattr(newitemtbl2, 'itog' + str(ind), itog)
                izm_exp_obl_list.append(newitemtbl2)

                newregrec = reg_exp_obl()
                newregrec._izm_exp_id = itemdoc.id
                newregrec._fkr_id = itemtbl2['_fkr_id']
                newregrec._spec_id = itemtbl2['_spec_id']
                newregrec._organization_id = org.id
                newregrec._date = date_object
                god = 0
                for ind in range(12, 0, -1):
                    sm = itemtbl2['sm' + str(ind)] if not itemtbl2['sm' + str(ind)] == None else 0
                    setattr(newregrec, 'sm' + str(ind), sm)
                    if (month == ind) and ((utv + sm) < 0):
                        ost = -sm
                        j = ind
                        while ost > 0 and j > 0:
                            utv_new = itemtbl1['utv' + str(j)] if not itemtbl1['utv' + str(j)] == None else 0
                            sum = min(utv_new, ost)
                            setattr(newregrec, 'sm' + str(j), -sum)
                            god += (-sum)
                            ost -= sum
                            j -= 1

                        if ost > 0:
                            transaction.rollback("Не хватает сумм в обязательствах. Проверьте суммы.")
                        break
                    else:
                        god += sm
                newregrec.god = god
                reg_exp_obl_list.append(newregrec)

            izm_exp_obl.objects.bulk_create(izm_exp_obl_list)
            reg_exp_obl.objects.bulk_create(reg_exp_obl_list)

            # ***********************************************************************************
            # **********ПРОВЕРКА ОСТАТКОВ ПОСЛЕ ЗАПИСИ ДОКУМЕНТА. *******************************
            # ***********************************************************************************
            query = f"""with    union_utv_izm as (SELECT 
                                            _fkr_id, 
                                            _spec_id, 
                                            _organization_id,
                                            sum(god) as god, 
                                            sum(sm1) as sm1, 
                                            sum(sm1 + sm2) as sm2, 
                                            sum(sm1 + sm2 + sm3) as sm3, 
                                            sum(sm1 + sm2 + sm3 + sm4) as sm4, 
                                            sum(sm1 + sm2 + sm3 + sm4 + sm5) as sm5, 
                                            sum(sm1 + sm2 + sm3 + sm4 + sm5 + sm6) as sm6, 
                                            sum(sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7) as sm7, 
                                            sum(sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8) as sm8, 
                                            sum(sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8 + sm9) as sm9, 
                                            sum(sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8 + sm9 + sm10) as sm10, 
                                            sum(sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8 + sm9 + sm10 + sm11) as sm11, 
                                            sum(sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8 + sm9 + sm10 + sm11 +sm12) as sm12 
                                        FROM public.docs_reg_exp_pay
                                        WHERE _organization_id = 1
                                        GROUP BY _fkr_id, _spec_id,_organization_id),
                                fkr as (SELECT * FROM public.dirs_fkr
                                                        WHERE id in (select _fkr_id from union_utv_izm)),
                                spec as (SELECT * FROM public.dirs_spec_exp
                                                        WHERE id in (select _spec_id from union_utv_izm))

                                SELECT  
                                    fulldata._fkr_id, 
                                    fulldata._spec_id,
                                    max(fkr.name_rus) as fkr_name, 
                                    max(spec.name_rus) as spec_name,
                                    max(fkr.code) as fkr_code, 
                                    max(spec.code) as spec_code,
                                    COALESCE(sum(god),0) as god, 
                                    COALESCE(sum(sm1),0) as sm1, 
                                    COALESCE(sum(sm2),0) as sm2,
                                    COALESCE(sum(sm3),0) as sm3, 
                                    COALESCE(sum(sm4),0) as sm4, 
                                    COALESCE(sum(sm5),0) as sm5, 
                                    COALESCE(sum(sm6),0) as sm6, 
                                    COALESCE(sum(sm7),0) as sm7, 
                                    COALESCE(sum(sm8),0) as sm8, 
                                    COALESCE(sum(sm9),0) as sm9, 
                                    COALESCE(sum(sm10),0) as sm10, 
                                    COALESCE(sum(sm11),0) as sm11, 
                                    COALESCE(sum(sm12),0) as sm12
                                FROM union_utv_izm as fulldata
                                left join fkr on
                                    fulldata._fkr_id = fkr.id
                                left join spec on
                                    fulldata._spec_id = spec.id
                                GROUP BY (_fkr_id, _spec_id)
                            """
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                res_pay = [dict(zip(columns, row))
                           for row in cursor.fetchall()]

            query = query.replace("docs_reg_exp_pay", "docs_reg_exp_obl")
            with connection.cursor() as cursor:
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                res_obl = [dict(zip(columns, row))
                           for row in cursor.fetchall()]

            if not len(res_obl) == len(res_pay):
                transaction.set_rollback(True)
                return HttpResponse(json.dumps({"status": "Обязательства и платежи в плане различаются. Проверьте планы в приложении 2-5"}), content_type="application/json", status=400)

            errormess = ""
            for i in range(0, len(res_obl)):
                if not res_obl[i]["sm12"] == res_pay[i]["sm12"]:
                    transaction.set_rollback(True)
                    return HttpResponse(json.dumps({"status": "Сумма обязательства и платежей не совпадают"}), content_type="application/json", status=400)

                for j in range(1, 13):
                    if res_obl[i]["sm" + str(j)] < res_pay[i]["sm" + str(j)]:
                        errormess = errormess + \
                            res_obl[i]["fkr_code"] + " - " + \
                            res_obl[i]["spec_code"] + " превышение! \n"
                        break

            if not errormess == "":
                transaction.set_rollback(True)
                return HttpResponse(json.dumps({"status": errormess}), content_type="application/json", status=400)

            return HttpResponse(json.dumps({"status": "Документ успешно записан", "id_doc":itemdoc.id, "nom":itemdoc.nom}), content_type="application/json", status=200)

    except Exception as e:
        response_data = {"status": e.args[0]}
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def izmexpdelete(request):
    req = json.loads(request.body)
    docs = req['mass_doc_id']
    shift = req['shift']
    is_admin = (request.user.groups.filter(name='fulldata').count()>0)
    if shift and is_admin:
        try:
            with transaction.atomic():
                for id in docs:
                    izm_exp_pay.objects.filter(_izm_exp_id=id).delete()
                    reg_exp_pay.objects.filter(_izm_exp_id=id).delete()
                    izm_exp_obl.objects.filter(_izm_exp_id=id).delete()
                    reg_exp_obl.objects.filter(_izm_exp_id=id).delete()
                    docobj = izm_exp.objects.get(id=id)
                    docobj.delete()   
        except Exception as err:
            a = 1
    else:
        try:
            with transaction.atomic():
                for id in docs:
                    izm_exp_pay.objects.filter(_izm_exp_id=id).update(deleted = True)
                    reg_exp_pay.objects.filter(_izm_exp_id=id).delete()
                    izm_exp_obl.objects.filter(_izm_exp_id=id).update(deleted = True)
                    reg_exp_obl.objects.filter(_izm_exp_id=id).delete()
                    docobj = izm_exp.objects.get(id=id)
                    docobj.deleted = True
                    docobj.save() 
        except Exception as err:
            a = 1

    return response.Response({"status":"успешно"})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def expgetplanbyclassif(request):
    datastr = request.body
    data = json.loads(datastr)
    # table = data['table']
    _organization = data['_organization']
    _fkr = data['_fkr']
    _spec = data['_spec']
    _date = data['_date']
    date = datetime.strptime(_date, "%d.%m.%Y %H:%M:%S")

    qset_fkr = fkr.objects.get(id=_fkr)
    qset_spec = spec_exp.objects.get(id=_spec)

    resp = {
        "pay": {
            "_fkr_id": qset_fkr.id,
            "_fkr_name": qset_fkr.name_rus,
            "_fkr_code": qset_fkr.code,
            "_spec_id": qset_spec.id,
            "_spec_name": qset_spec.name_rus,
            "_spec_code": qset_spec.code
            },
        "obl": {
            "_fkr_id": qset_fkr.id,
            "_fkr_name": qset_fkr.name_rus,
            "_fkr_code": qset_fkr.code,
            "_spec_id": qset_spec.id,
            "_spec_name": qset_spec.name_rus,
            "_spec_code": qset_spec.code
            }
    }

    query_pay = f"""with union_utv_izm as (SELECT _fkr_id, _spec_id, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12 
                            FROM public.docs_reg_exp_pay
                            WHERE _organization_id = {_organization} and _date>=DATE_TRUNC('year', current_date) and _date<='{date}' and _fkr_id = {_fkr} and _spec_id = {_spec}
                            GROUP BY _fkr_id, _spec_id)
                    SELECT  
                        COALESCE(sum(sm1),0) as utv1, 
                        COALESCE(sum(sm2),0) as utv2,
                        COALESCE(sum(sm3),0) as utv3, 
                        COALESCE(sum(sm4),0) as utv4, 
                        COALESCE(sum(sm5),0) as utv5, 
                        COALESCE(sum(sm6),0) as utv6, 
                        COALESCE(sum(sm7),0) as utv7, 
                        COALESCE(sum(sm8),0) as utv8, 
                        COALESCE(sum(sm9),0) as utv9, 
                        COALESCE(sum(sm10),0) as utv10, 
                        COALESCE(sum(sm11),0) as utv11, 
                        COALESCE(sum(sm12),0) as utv12,
                        0 as sm1, 0 as sm2, 0 as sm3, 0 as sm4, 0 as sm5, 0 as sm6, 0 as sm7, 0 as sm8, 0 as sm9, 0 as sm10, 0 as sm11, 0 as sm12,
                        0 as itog1, 0 as itog2, 0 as itog3, 0 as itog4, 0 as itog5, 0 as itog6, 0 as itog7, 0 as itog8, 0 as itog9, 0 as itog10, 0 as itog11, 0 as itog12
                    FROM union_utv_izm                
                    GROUP BY _fkr_id,_spec_id"""

    with connection.cursor() as cursor:
        cursor.execute(query_pay)
        columns = [col[0] for col in cursor.description]
        result_pay = [dict(zip(columns, row))
                  for row in cursor.fetchall()]

    if len(result_pay) > 0:
        resp['pay'] = {**resp['pay'], **result_pay[0]}
    else:
        for ind in range(1, 13):
            resp['pay']["utv" + str(ind)] = 0
            resp['pay']["sm" + str(ind)] = 0
            resp['pay']["itog" + str(ind)] = 0



    query_obl = f"""with union_utv_izm as (SELECT _fkr_id, _spec_id, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12 
                            FROM public.docs_reg_exp_obl
                            WHERE _organization_id = {_organization} and _date>=DATE_TRUNC('year', current_date) and _date<='{date}' and _fkr_id = {_fkr} and _spec_id = {_spec}
                            GROUP BY _fkr_id, _spec_id)
                    SELECT  
                        COALESCE(sum(sm1),0) as utv1, 
                        COALESCE(sum(sm2),0) as utv2,
                        COALESCE(sum(sm3),0) as utv3, 
                        COALESCE(sum(sm4),0) as utv4, 
                        COALESCE(sum(sm5),0) as utv5, 
                        COALESCE(sum(sm6),0) as utv6, 
                        COALESCE(sum(sm7),0) as utv7, 
                        COALESCE(sum(sm8),0) as utv8, 
                        COALESCE(sum(sm9),0) as utv9, 
                        COALESCE(sum(sm10),0) as utv10, 
                        COALESCE(sum(sm11),0) as utv11, 
                        COALESCE(sum(sm12),0) as utv12,
                        0 as sm1, 0 as sm2, 0 as sm3, 0 as sm4, 0 as sm5, 0 as sm6, 0 as sm7, 0 as sm8, 0 as sm9, 0 as sm10, 0 as sm11, 0 as sm12,
                        0 as itog1, 0 as itog2, 0 as itog3, 0 as itog4, 0 as itog5, 0 as itog6, 0 as itog7, 0 as itog8, 0 as itog9, 0 as itog10, 0 as itog11, 0 as itog12
                    FROM union_utv_izm                
                    GROUP BY _fkr_id,_spec_id"""

    with connection.cursor() as cursor:
        cursor.execute(query_obl)
        columns = [col[0] for col in cursor.description]
        result_obl = [dict(zip(columns, row))
                  for row in cursor.fetchall()]
                  
    if len(result_obl) > 0:
        resp['obl'] = {**resp['obl'], **result_obl[0]}
    else:
        for ind in range(1, 13):
            resp['obl']["utv" + str(ind)] = 0
            resp['obl']["sm" + str(ind)] = 0
            resp['obl']["itog" + str(ind)] = 0
    
    json_data = json.dumps(resp, ensure_ascii=False)
    return HttpResponse(json_data, content_type="application/json")





# ****************************************************************
# ***Сервисы документа свода по расходам***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def svodexplist(request):
    queryset = getqsetlist(svod_exp, request.user, 'nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = svod_exp_list_serial(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def svodexpadd(request):
    datastr = request.body
    data = json.loads(datastr)
    id_doc = data['id']

    try:
        with transaction.atomic():
            if id_doc==0:
                cnt = svod_exp.objects.filter(_organization_id = data['_organization']['id']).count()
                doc = svod_exp()
                doc.nom = str(cnt + 1)
            else:
                doc = svod_exp.objects.get(id=id_doc)
                if doc.deleted:
                    tbl = svod_exp_tbl.objects.filter(_svod_exp_id = doc.id)
                    reg_svod_exp.objects.filter(_svod_exp_id = doc.id).delete()
                    for item in tbl:
                        item.deleted = False
                        item.save()

                        new = reg_svod_exp()
                        new._izm_exp_id = item._izm_exp_id
                        new._svod_exp_id = doc.id
                        new._organization_id = data['_organization']['id']
                        new._date = datetime.strptime(data['_date'], '%d.%m.%Y %H:%M:%S')
                        new.save()

            doc._date = datetime.strptime(data['_date'], '%d.%m.%Y %H:%M:%S')
            doc._organization_id = data['_organization']['id']
            doc.deleted = False
            doc.save()

            return HttpResponse(json.dumps({"status": "Успешно записан", "doc_id":doc.id, "nom":doc.nom}), content_type="application/json", status=200)
    except Exception as err:
        return response.Response({"status":"Ошибка добавления документа."})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def svodexpitem(request, id_doc):
    if id_doc == 0:
        org = request.user.profile._organization
        jsondata = {
                "doc": {
                    "id": 0,
                    "nom": "",
                    "_date": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
                    "deleted": False,
                    "_organization": {
                        "id": org.id,
                        "name_rus": org.name_rus
                    }
                },
                "payments":[],
                "obligats":[],
                "docs_izm":[]
            }
    else:
        jsondata = object_svod_get(id_doc=id_doc)
        
    return response.Response(jsondata)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def svodexp_add_doc(request, id_doc):
    
    try:
        with transaction.atomic():
            datastr = request.body
            data = json.loads(datastr)
            doc_izm = izm_exp.objects.get(id = data['doc_id'])
            tbl = svod_exp_tbl()
            tbl._date = doc_izm._date
            tbl._izm_exp = doc_izm
            tbl._organization = doc_izm._organization
            tbl._svod_exp_id = id_doc
            tbl.save()

            reg = reg_svod_exp()
            reg._izm_exp_id = data['doc_id']
            reg._svod_exp_id = id_doc
            reg._organization = doc_izm._organization
            reg._date = doc_izm._date
            reg.save()

            jsondata = object_svod_get(id_doc=id_doc)
            return response.Response(jsondata)
    except Exception as err:
        return response.Response({"status":"Ошибка добавления документа."})
    


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def svodexp_del_doc(request, id_doc):
    try:
        with transaction.atomic():
            datastr = request.body
            data = json.loads(datastr)
            tbl = svod_exp_tbl.objects.get(id = data['doc_id'])
            if tbl._svod_exp_id == id_doc:
                tbl.delete()  

            reg_svod_exp.objects.filter(_svod_exp_id = id_doc, _izm_exp_id = tbl._izm_exp_id).delete()

            jsondata = object_svod_get(id_doc=id_doc)
            return response.Response(jsondata)
    except Exception as err:
        return response.Response({"status":"Ошибка удаления документа."})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def svodexpdelete(request):
    req = json.loads(request.body)
    docs = req['mass_doc_id']
    shift = req['shift']
    is_admin = (request.user.groups.filter(name='fulldata').count()>0)

    errors = ''
    if shift and is_admin:
        try:
            with transaction.atomic():
                for id_doc in docs:
                    svod_exp_tbl.objects.filter(_svod_exp_id=id_doc).delete()
                    reg_svod_exp.objects.filter(_svod_exp_id=id_doc).delete()
                    docdel = svod_exp.objects.get(id=id_doc)
                    docdel.delete()   
        except Exception as err:
            errors = 'Ошибка удаления документа'
    else:
        try:
            with transaction.atomic():
                for id_doc in docs:
                    tbldel = svod_exp_tbl.objects.filter(_svod_exp_id=id_doc)
                    for item in tbldel:
                        item.deleted = True
                        item.save()
                    docdel = svod_exp.objects.get(id=id_doc)
                    docdel.deleted = True
                    docdel.save()  
                    reg_svod_exp.objects.filter(_svod_exp_id=id_doc).delete() 
        except Exception as err:
            errors = 'Ошибка удаления документа'

    if errors=='':
        return response.Response({"status":"успешно"})
    else:
        return response.Response({"status":"Ошибка удаления документа"}, status=400)



# ****************************************************************
# *****Сервисы импорт по поступлениям 2-19*****
# ****************************************************************
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_219(request):
    jsreq = json.loads(request.body)
    filesname = jsreq['file']
    _organization_id = request.user.profile._organization_id

    for filen in filesname:
        buffer = base64.b64decode(filen.replace("data:application/pdf;base64,",""))
        pdf_file = io.BytesIO(buffer)
        pdfreader = PdfReader(pdf_file)
        x=len(pdfreader.pages)

        mass_obj = []
        mass_kp = []
        

        kp_count = 0
        kp = ""
        for num in range(0, x):
            pageobj = pdfreader.pages[num]
            text=pageobj.extract_text().split('\n')

            if not text[0] == 'Форма № 2-19':
                return "not 2-19 file"

            if num == 0:
                _date = text[3].split(':')[1]
                date = datetime.strptime(_date, '%d.%m.%Y')
                _budjet = text[4].split(': ')[1].split(' -')[0]
                budjet_name = text[4]

            for i in range(5, len(text)):
                str = text[i]

                if not kp=="":
                    # Данная строка выяснит, содержит ли цифры. Если не содержит то возвращает пустую строку
                    value = ''.join(char for char in text[i] if char.isdigit())
                    if value == "":
                        # Если не содержит цифры, то следующий цикл
                        continue
                    else:
                        # иначе это значит что это нужные нам суммы
                        s = text[i]
                        mass_item = s.split(' ')
                        mas_sum = []
                        for itm in mass_item:
                            tmp = ''.join(char for char in itm if char.isdigit())
                            if tmp=='':
                                continue
                            else:
                                sm = float(itm.replace(',', '').replace('район','').replace('а',''))
                                mas_sum.append(sm)

                        kp_db = kp[0] + '/' + kp[1] + kp[2] + '/' + kp[3] + '/' + kp[4] + kp[5]
                        
                        if len(mas_sum)<10:
                            continue

                        obj = {
                            "kp": kp_db,
                            "sm1": mas_sum[0],
                            "sm2": mas_sum[1],
                            "sm3": mas_sum[2],
                            "sm4": mas_sum[3],
                            "sm5": mas_sum[4],
                            "sm6": mas_sum[5],
                            "sm7": mas_sum[6],
                            "sm8": mas_sum[7],
                            "sm9": mas_sum[8],
                            "sm10": mas_sum[9],
                        }

                        mass_obj.append(obj)
                        mass_kp.append(kp_db)

                        kp = ""
                        continue


                # Здесь сначала определеяется КП, потом код сверху (суммы определяются)
                try:
                    mas = str.split(' ')
                    value = mas[1].replace(' ', '')
                    if value.isdigit() and len(value)==6:
                        kp = str.split(" ")[1].replace(" ", "")
                        kp_count += 1
                except:
                    continue

        # ****************************************************************
        # ***ЗДЕСЬ УЖЕ НЕПОСРЕДСТВЕННО ЗАПИСЬ КОРРЕКТНО СЧИТАННЫХ ДАННЫХ**
        # ****************************************************************
        query = f"""SELECT id, code FROM public.dirs_classification_income
                    WHERE code in {tuple(mass_kp)}"""

        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row))
                    for row in cursor.fetchall()]

        try:
            with transaction.atomic():
                qset_bjt = budjet.objects.filter(code = _budjet)
                _budjet_id = 0
                for bjt in qset_bjt:
                    _budjet_id = bjt.id

                if _budjet_id == 0:
                    newbjt = budjet()
                    newbjt.code = _budjet
                    newbjt.name_kaz = budjet_name
                    newbjt.name_rus = budjet_name
                    newbjt.save()
                    _budjet_id = newbjt.id

                exist_doc = import219.objects.filter(_date = date, _budjet_id = _budjet_id).count()
                if exist_doc>0:
                    transaction.rollback("Такой документ уже загружен")

                newdoc = import219()
                newdoc.nom = '12'
                newdoc._date = date
                newdoc._budjet_id = _budjet_id
                newdoc._organization_id = _organization_id
                newdoc.save()

                bulk_mass = []
                for item in mass_obj:
                    newzap = import219_tbl1()
                    newzap._import219_id = newdoc.id
                    newzap._date = date
                    newzap._budjet_id = _budjet_id
                    newzap._organization_id = _organization_id

                    newzap.sm1 = item['sm1']
                    newzap.sm2 = item['sm2']
                    newzap.sm3 = item['sm3']
                    newzap.sm4 = item['sm4']
                    newzap.sm5 = item['sm5']
                    newzap.sm6 = item['sm6']
                    newzap.sm7 = item['sm7']
                    newzap.sm8 = item['sm8']
                    newzap.sm9 = item['sm9']
                    newzap.sm10 = item['sm10']

                    kp_bd_id = 0
                    for sr in result:
                        if sr['code'] == item['kp']:
                            kp_bd_id = sr['id']
                            break

                    
                    # Если такой классификации поступления нету, то добавляем
                    if kp_bd_id == 0:
                        qset_cat = category_income.objects.filter(code = item['kp'][0])
                        cat_id = 0
                        for itm in qset_cat:
                            cat_id = itm.id

                        if cat_id == 0:
                            cat1 = category_income()
                            cat1.code = item['kp'][0]
                            cat1.name_kaz = "добавлено автоматический при импорте 2-19"
                            cat1.name_rus = "добавлено автоматический при импорте 2-19"
                            cat1.save()
                            cat_id = cat1.id

                        qset_cat = class_income.objects.filter(code = (item['kp'][2] + item['kp'][3]))
                        clas_id = 0
                        for itm in qset_cat:
                            clas_id = itm.id
                        if clas_id == 0:
                            classs = class_income()
                            classs.code = item['kp'][2] + item['kp'][3]
                            classs.name_kaz = "добавлено автоматический при импорте 2-19"
                            classs.name_rus = "добавлено автоматический при импорте 2-19"
                            classs.save()
                            clas_id = classs.id

                        qset_cat = podclass_income.objects.filter(code = item['kp'][5])
                        podcl_id = 0
                        for itm in qset_cat:
                            podcl_id = itm.id
                        if podcl_id == 0:
                            podcl = podclass_income()
                            podcl.code = item['kp'][5]
                            podcl.name_kaz = "добавлено автоматический при импорте 2-19"
                            podcl.name_rus = "добавлено автоматический при импорте 2-19"
                            podcl.save()
                            podcl_id = podcl.id

                        qset_cat = spec_income.objects.filter(code = (item['kp'][7] + item['kp'][8]))
                        spec_id = 0
                        for itm in qset_cat:
                            spec_id = itm.id
                        if spec_id == 0:
                            spec = spec_income()
                            spec.code = item['kp'][7] + item['kp'][8]
                            spec.name_kaz = "добавлено автоматический при импорте 2-19"
                            spec.name_rus = "добавлено автоматический при импорте 2-19"
                            spec.save()
                            spec_id = spec.id


                        classific = classification_income()
                        classific._category_id = cat_id
                        classific._classs_id = clas_id
                        classific._podclass_id = podcl_id
                        classific._spec_id = spec_id
                        classific.code = item['kp']
                        classific.name_kaz = "добавлено автоматический при импорте 2-19"
                        classific.name_rus = "добавлено автоматический при импорте 2-19"
                        classific.save()
                        kp_bd_id = classific.id

                    newzap._classification_id = kp_bd_id
                    bulk_mass.append(newzap)

                import219_tbl1.objects.bulk_create(bulk_mass)
        except Exception as e:  
            print(e.args[0])
            continue
    return HttpResponse('{"status": "данные успешно записаны"}', content_type="application/json", status = 200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import219list(request):
    queryset = getqsetlist(import219, request.user, 'nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = import_219_serial(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import219item(request, id_doc):
    queryset = type_izm_doc.objects.all()
    qset = import219.objects.get(id = id_doc)
    serial = import_219_serial(qset, many = False)

    query = f"""with tbl as (SELECT _classification_id, sm1, sm2, sm3, sm4, sm5, sm6, sm7, sm8, sm9, sm10 FROM public.docs_import219_tbl1
                                WHERE _import219_id={id_doc}),
                        classif as (SELECT id, code, name_rus as name FROM public.dirs_classification_income
                                    WHERE id in (select _classification_id from tbl))
                    select _classification_id, max(code) as code, max(name) as name, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, 
                    sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10 from tbl
                    left join classif
                    on tbl._classification_id = classif.id
                    group by rollup(_classification_id)
                    order by _classification_id nulls last, code"""


    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
            for row in cursor.fetchall()]

    jsondata = {
                    "doc": serial.data,
                    "table": result
                }
    return response.Response(jsondata)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def import219delete(request):
    req = json.loads(request.body)
    docs = req['mass_doc_id']
    shift = req['shift']
    is_admin = (request.user.groups.filter(name='fulldata').count()>0)
    if shift and is_admin:
        try:
            with transaction.atomic():
                for id_doc in docs:
                    tbldel = import219_tbl1.objects.filter(_import219_id=id_doc)
                    for item in tbldel:
                        item.delete()
                    docdel = import219.objects.get(id=id_doc)
                    docdel.delete()   
        except Exception as err:
            a = 1
    else:
        try:
            with transaction.atomic():
                for id_doc in docs:
                    tbldel = import219_tbl1.objects.filter(_import219_id=id_doc)
                    for item in tbldel:
                        item.deleted = True
                        item.save()
                    docdel = import219.objects.get(id=id_doc)
                    docdel.deleted = True
                    docdel.save()   
        except Exception as err:
            a = 1

    return response.Response({"status":"успешно"})





# ****************************************************************
# *****Сервисы импорт по расходам 4-20*****
# ****************************************************************
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_420(request):
    jsreq = json.loads(request.body)
    filesname = jsreq['file']
    errors_txt = ""
    for filen in filesname:
        buffer = base64.b64decode(filen.replace("data:application/pdf;base64,",""))
        pdf_file = io.BytesIO(buffer)
        pdfreader = PdfReader(pdf_file)

        # pdffileobj = open("../imports/420/2502.pdf", 'rb')
        # pdfreader = PdfReader(pdffileobj)

        x = len(pdfreader.pages)

        abp_ = ""
        bp = ""
        podpr = ""
        spec = ""
        itogsums = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]

        mass_res = []
        mass_fkr = []
        mass_spec = []
        for num in range(0, x):
            pageobj = pdfreader.pages[num]
            text = pageobj.extract_text().split('\n')
            if num == 0:
                start_item = 15
                _date = text[3].split(' ')[1]
                budjet_code = text[6].split(' ')[1]
                budjet_name = text[6].split(':')[1].replace(' ', '')
                org = text[10].split(':')[1].split('-')[0].replace(' ','')
                abp_code_str = org[0:3]
                org_code = org[3:7]
                org_name = text[10].split(':')[1].split('-')[1]
            else:
                start_item = 0

            if not text[0] == 'Форма № 4-20':
                return "not 4-20 file"

            
            for i in range(len(text)):
                sums = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]       

                if i >= start_item:
                    count = 0
                    prostotext = False
                    str1 = text[i]

                    for char in str1:
                        if char.isspace():
                            count += 1
                        else:
                            if (char in ('1234567890')):
                                if not len(str1.split(' ')[count]) == 3:
                                    prostotext = True
                                break  
                            else:
                                prostotext = True
                                break

                    if prostotext:
                        continue

                    if (count == 0):
                        abp_ = ""
                    elif (count == 3):
                        bp = ""
                    elif (count == 7):
                        podpr = ""
                    elif (count == 12):
                        spec = ""

                    # ищем АБП
                    if abp_ == "":
                        abp_ = text[i].split(' ')[0]

                    # ищем БП
                    elif not abp_ == "" and bp == "":
                        bp = text[i].split(' ')[3]

                    elif not bp == "" and podpr == "":
                        podpr = text[i].split(' ')[7]

                    elif not podpr == "" and spec == "":
                        spec = text[i].split(' ')[12]
                        if (text[i].split()[len(text[i].split())-1][-1] in ('1234567890')):
                            item = i
                        else:
                            item = i + 1

                        for y in range(10, 0, -1):
                            txt = text[item].split()[len(text[item].split())-y]
                            try:
                                sums[10 - y] = float(txt.replace(',', ''))
                            except:
                                sums[10 - y] = float(''.join(char for char in txt if char.isdigit() or char == '.'))
                            itogsums[10-y] = itogsums[10 - y] + sums[10 - y]

                        mass_fkr.append(abp_+'/'+bp+'/'+podpr)
                        mass_spec.append(spec)
                        mass_res.append({
                            "fkr":abp_+'/'+bp+'/'+podpr,
                            "_fkr_id":0,
                            "abp": abp_,
                            "pr":bp,
                            "ppr":podpr,
                            "spec":spec,
                            "_spec_id":0,
                            "sum":sums
                        })
                        

        # ПОИСК В БАЗЕ ДАННЫХ ФКР, ЕСЛИ НЕТ ТО СОЗДАЕМ
        qset_fkr = f"""SELECT id, code FROM public.dirs_fkr
                    WHERE code IN {tuple(mass_fkr)}"""
        with connection.cursor() as cursor:
                cursor.execute(qset_fkr)
                columns = [col[0] for col in cursor.description]
                res_fkr = [dict(zip(columns, row))
                        for row in cursor.fetchall()]

        for ind, item in enumerate(mass_fkr):
            find = False
            for j in res_fkr:
                if item==j['code']:
                    find = True 
                    _fkr_id = j['id']
                    break
            if find == False:
                # search ABP
                qset = f"""SELECT id FROM public.dirs_abp WHERE code = '{mass_res[ind]['abp']}'"""
                with connection.cursor() as cursor:
                    cursor.execute(qset)
                    res_abp = cursor.fetchall()

                qset = f"""SELECT id FROM public.dirs_program WHERE code like '%{mass_res[ind]['abp'] + '/' + mass_res[ind]['pr']}%'"""
                with connection.cursor() as cursor:
                    cursor.execute(qset)
                    res_bp = cursor.fetchall()

                qset = f"""SELECT id FROM public.dirs_podprogram WHERE code like '%{mass_res[ind]['abp'] + '/' + mass_res[ind]['pr']  + '/' + mass_res[ind]['ppr']}%'"""
                with connection.cursor() as cursor:
                    cursor.execute(qset)
                    res_ppr = cursor.fetchall()


                if len(res_abp)==0:
                    newabp = abp()
                    newabp.code = mass_res[ind]['abp']
                    newabp.name_rus = ''
                    newabp.name_kaz = ''
                    newabp.save()
                    _abp_id = newabp.id
                else:
                    _abp_id = res_abp[0][0]

                if len(res_bp)==0:
                    newpr = program()
                    newpr.code = '01/1/' + mass_res[ind]['abp'] + '/' + mass_res[ind]['pr']
                    newpr.name_rus = ''
                    newpr.name_kaz = ''
                    newpr._abp_id = _abp_id
                    newpr._funcpodgroup_id = 233
                    newpr.save()
                    _pr_id = newpr.id
                else:
                    _pr_id = res_bp[0][0]


                if len(res_ppr)==0:
                    newppr = podprogram()
                    newppr.code = '01/1/' + mass_res[ind]['abp'] + '/' + mass_res[ind]['pr'] + '/' + mass_res[ind]['ppr']
                    newppr.name_rus = ''
                    newppr.name_kaz = ''
                    newppr._abp_id = _abp_id
                    newppr._funcgroup_id = 32
                    newppr._funcpodgroup_id = 233
                    newppr._program_id = _pr_id
                    newppr.save()
                    _ppr_id = newppr.id
                else:
                    _ppr_id = res_ppr[0][0]

                newfkr = fkr()
                newfkr.code = mass_res[ind]['abp'] + '/' + mass_res[ind]['pr'] + '/' + mass_res[ind]['ppr']
                newfkr.name_rus = ''
                newfkr.name_kaz = ''
                newfkr._abp_id = _abp_id
                newfkr._funcgroup_id = 32
                newfkr._funcpodgroup_id = 233
                newfkr._program_id = _pr_id
                newfkr._podprogram_id = _ppr_id
                newfkr.save()
                _fkr_id = newfkr.id

            mass_res[ind]['_fkr_id'] = _fkr_id
            
            
    
        # ПОИСК В БАЗЕ ДАННЫХ СПЕЦИФИК(экр), ЕСЛИ НЕТ ТО СОЗДАЕМ
        qset_spec = f"""SELECT id, code FROM public.dirs_spec_exp
                    WHERE code IN {tuple(mass_spec)}"""
        with connection.cursor() as cursor:
                cursor.execute(qset_spec)
                columns = [col[0] for col in cursor.description]
                res_spec = [dict(zip(columns, row))
                        for row in cursor.fetchall()]
        for ind, item in enumerate(mass_spec):
            find = False
            for j in res_spec:
                if item==j['code']:
                    find = True 
                    _spec_id = j['id']
                    break
            if find == False:
                newspec = spec_exp()
                newspec.code = item
                newspec.name_rus = ''
                newspec.name_kaz = ''
                newspec.save()
                _spec_id = newspec.id
            
            mass_res[ind]['_spec_id'] = _spec_id
    
        
        try:
            with transaction.atomic():
                date = datetime.strptime(_date, '%d.%m.%Y')
                try:
                    org_id = organization.objects.get(codeorg = org_code).id
                except:
                    transaction.rollback("Организации с кодом " + org_code + " нет в базе данных или их несколько")

                try:
                    budjet_id = budjet.objects.get(code = budjet_code).id
                except:
                    budjet_id = 0
                if budjet_id == 0:
                    newbjt = budjet()
                    newbjt.code = budjet_code
                    newbjt.name_rus = budjet_name
                    newbjt.name_kaz = budjet_name
                    newbjt.save()
                    budjet_id = newbjt.id

                obj420_count = import420.objects.filter(_date = date, _organization_id = org_id).count()
                if obj420_count > 0:
                    transaction.rollback("Документ организации " + org_code + " уже загружен датой " + _date)

                count = import420.objects.filter(_organization_id = org_id).count()



                # СОЗДАНИЕ НОВОГО ДОКУМЕНТА 4-20
                new420 = import420()
                new420._date = date
                new420.nom = str(count+1)
                new420._organization_id = org_id
                new420._budjet_id = budjet_id
                new420.save()

                # Запись табличной части в базу данных
                mass_lines = []
                for line in mass_res:
                    newline = import420_tbl1()
                    newline._import420_id = new420.id
                    newline._fkr_id = line['_fkr_id']
                    newline._spec_id = line['_spec_id']
                    newline._budjet_id = budjet_id
                    newline._organization_id = org_id
                    newline._date = date
                    for i, sm in enumerate(line['sum']):
                        setattr(newline, 'sm' + str(i+1), sm)
                    mass_lines.append(newline)
                import420_tbl1.objects.bulk_create(mass_lines)


            
        except Exception as e:  
            errors_txt = errors_txt + e.args[0] + ','
            errors_txt = errors_txt.replace("'", "")
            errors_txt = errors_txt.replace("The connection", "")
            errors_txt = errors_txt.replace(" doesnt exist.", "")

    if errors_txt == "":
        return HttpResponse('{"status": "данные успешно записаны"}', content_type="application/json", status = 200)
    else:
        return HttpResponse('{"status": "' + errors_txt + '"}', content_type="application/json", status = 400)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import420list(request):
    queryset = getqsetlist(import420, request.user, 'nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = import_420_serial(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import420item(request, id_doc):
    qset = import420.objects.get(id = id_doc)
    serial = import_420_serial(qset, many = False)

    query = f"""with tbl as (SELECT _fkr_id, _spec_id, sm1, sm2, sm3, sm4, sm5, sm6, sm7, sm8, sm9, sm10 FROM public.docs_import420_tbl1
                                WHERE _import420_id={id_doc}),
                        fkr as (SELECT id, code as code_fkr, name_rus as name_fkr FROM public.dirs_fkr
                                    WHERE id in (select _fkr_id from tbl)),
						spec as (SELECT id, code as code_spec, name_rus as name_spec FROM public.dirs_spec_exp
                                    WHERE id in (select _spec_id from tbl))
                select _fkr_id, max(code_fkr) as code_fkr, max(name_fkr) as name_fkr, _spec_id, max(code_spec) as code_spec, max(name_spec) as name_spec, 
                sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10 from tbl
                left join fkr
                on tbl._fkr_id = fkr.id
                left join spec
                on tbl._spec_id = spec.id
                group by _fkr_id, _spec_id
                order by code_fkr, code_spec"""


    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
            for row in cursor.fetchall()]

    jsondata = {
                    "doc": serial.data,
                    "table": result
                }
    return response.Response(jsondata)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def import420delete(request):
    req = json.loads(request.body)
    docs = req['mass_doc_id']
    shift = req['shift']
    is_admin = (request.user.groups.filter(name='fulldata').count()>0)
    if shift and is_admin:
        try:
            with transaction.atomic():
                for id_doc in docs:
                    tbldel = import420_tbl1.objects.filter(_import420_id=id_doc).delete()
                    docdel = import420.objects.get(id=id_doc)
                    docdel.delete()   
        except Exception as err:
            a = 1
    else:
        try:
            with transaction.atomic():
                for id_doc in docs:
                    tbldel = import420_tbl1.objects.filter(_import420_id=id_doc)
                    for item in tbldel:
                        item.deleted = not item.deleted
                        item.save()
                    docdel = import420.objects.get(id=id_doc)
                    docdel.deleted = not docdel.deleted
                    docdel.save()   
        except Exception as err:
            a = 1

    return response.Response({"status":"успешно"})




