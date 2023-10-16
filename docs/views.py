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
from .shareModuleInc import *



class CustomPagination(pagination.LimitOffsetPagination):
    default_limit = 25  # Количество объектов на странице по умолчанию
    max_limit = 50     # Максимальное количество объектов на странице


# ****************************************************************
# ***Сервисы утвержденного плана финансирования по поступлениям***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvinclist(request):
    queryset = utv_inc.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_inc_Serializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvincitem(request, id):

    if (id==0):
        try:
            org = profile.objects.get(_user_id = request.user.pk)._organization
        except:
            response_data = {"status": "Не указана текущая организация в профиле пользователя"}
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

        resp = {
                    "doc": {
                        "id": 0,
                        "_organization": {
                            "id": org.id,
                            "name_rus": org.name_rus,
                            "name_kaz":org.name_kaz
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
                doc_cnt = utv_inc.objects.filter(_date__year=year, _organization_id=org.id).count()
                itemdoc = utv_inc()
                itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            else:
                itemdoc = utv_inc.objects.get(id=doc_req['id'])

            itemdoc._organization_id = org.id
            itemdoc._budjet_id = org._budjet.id
            itemdoc._date = date_object
            itemdoc.save()

            
            #Очищаем предыдущие записи табличной части
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
                    sm = itemtbl1['sm'+str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    god += sm
                    setattr(newitemtbl1, 'sm' + str(ind), sm)
                newitemtbl1.god = god
                # newitemtbl1.save()
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
                rows_save_reg.append(reg_new_rec) # Помещаем в массив строки для дальнейшей записи за одно обращение

            utv_inc_tbl1.objects.bulk_create(rows_save_tbl)
            reg_inc.objects.bulk_create(rows_save_reg)
    

    except Exception as e:
        return HttpResponse('{"status": "Ошибка сохранения документа"}', content_type="application/json", status=400)

    # Документ сам (шапка документа)
    queryset_doc = utv_inc.objects.get(id=itemdoc.id)
    serialdoc = utv_inc_Serializer(queryset_doc)
    # табличная часть
    queryset_tbl1 = utv_inc_tbl1.objects.filter(_utv_inc_id=queryset_doc.id)
    serial_tbl1 = utv_inc_tbl1_Serializer(queryset_tbl1, many=True)

    # Возвращаем шапку и табличную часть в одном объекте
    resp = {'doc': serialdoc.data,
            'tbl1': serial_tbl1.data}
    return response.Response(resp)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def utvincdelete(request, id):
    try:
        docobj = utv_inc.objects.get(id=id)
        docobj.deleted = not docobj.deleted
        docobj.save()

        # табличная часть
        tbl1objs = utv_inc_tbl1.objects.filter(_utv_inc_id=docobj.id)
        for itmtbl1 in tbl1objs:
            itmtbl1.deleted = not itmtbl1.deleted
            itmtbl1.save()
    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status=400)

    queryset = utv_inc.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_inc_Serializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


# ****************************************************************
# *****Сервисы изменения плана финансирования по поступлениям*****
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izminclist(request):
    queryset = izm_inc.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_inc_Serializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmincitem(request, id):

    queryset = type_izm_doc.objects.all()
    serialtype = typedocSerializer(queryset, many=True)

    if (id==0):
        try:
            org = profile.objects.get(_user_id = request.user.pk)._organization
        except:
            response_data = {"status": "Не указана текущая организация в профиле пользователя"}
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

        resp = {
                    "doc": {
                        "id": 0,
                        "_organization": {
                            "id": org.id,
                            "name_rus": org.name_rus,
                            "name_kaz":org.name_kaz
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
    bjt_id = doc_req['_organization']['_budjet']['id']
    doc_id = doc_req['id']

    try:
        with transaction.atomic():
            # Запис шапки документа изменения по поступлениям
            date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
            org = organization.objects.get(id=org_id)

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
            # Непосредственно сохранение документа
            itemdoc.save()


            #Очищаем предыдущие записи табличной части
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
                    utv = itemtbl1['utv' +
                        str(ind)] if not itemtbl1['utv' + str(ind)] == None else 0
                    sm = itemtbl1['sm' +
                        str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    itog = itemtbl1['itog' +
                        str(ind)] if not itemtbl1['itog' + str(ind)] == None else 0

                    # Проверка изменения сумм на предыдущие месяцы. Если изменения есть, то отменяем транзакцию и возвращаем ошибку.
                    if ind < date_object.month:
                        if not (sm == 0):
                            transaction.set_rollback(True)
                            return HttpResponse('{"status": "Ошибка, нельзя менять предыдущие месяцы!!"}', content_type="application/json", status=400)
                    # Проверка изменения сумм на последующие месяцы. Сумма не должна превышать остатка на текущий месяц.
                    if ind > date_object.month:
                        if (utv + sm) < 0:
                            transaction.set_rollback(True)
                            return HttpResponse('{"status": "Ошибка, Сумма больше остатка!!"}', content_type="application/json", status=400)

                    # Если ошибок нет, то заполняем значения своиств за 12 месяцев
                    setattr(newitemtbl1, 'utv' + str(ind), utv)
                    setattr(newitemtbl1, 'sm' + str(ind), sm)
                    setattr(newitemtbl1, 'itog' + str(ind), itog)
                rows_save.append(newitemtbl1) # Помещаем в массив строки для дальнейшей записи за одно обращение



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
                rows_save_reg.append(reg_new_rec) # Помещаем в массив строки для дальнейшей записи за одно обращение


            izm_inc_tbl1.objects.bulk_create(rows_save)
            reg_inc.objects.bulk_create(rows_save_reg)










            


            list_clasif = ''
            for itm in tbl1_req:
                if list_clasif == '':
                    list_clasif = str(itm['_classification']['id'])
                    continue
                list_clasif = list_clasif + ', ' + \
                    str(itm['_classification']['id'])

            date = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
            date_start = datetime.strptime(
                str(date.year) + "-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
            dateend = date

            query = f"""with 
                        izm as (SELECT _classification_id,  sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12
                                FROM public.docs_izm_inc_tbl1
                                where  _izm_inc_id = {doc_id} and  _organization_id = {org_id} and not deleted and _date>='{date_start}' and _date <= '{dateend}' and _classification_id in ({list_clasif})
                                group by _classification_id),            
                        sm as (SELECT _classification_id, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12
                                FROM public.docs_utv_inc_tbl1
                                where _organization_id = {org_id} and not deleted and _date>='{date_start}' and _date <= '{dateend}' and _classification_id in ({list_clasif})
                                group by _classification_id),
                        
                        union_sm_izm as (select * from sm
                                            union all
                                            select * from izm),
                        classname as (SELECT * FROM public.dirs_classification_income
                                     WHERE id in ({list_clasif}))
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
                    FROM union_sm_izm
                    RIGHT JOIN classname
                    ON _classification_id = classname.id
                    GROUP BY _classification, classification_code, classification_name
                    ORDER BY _classification"""

            with connection.cursor() as cursor:
                cursor.execute(query)
                # asd = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                result = [dict(zip(columns, row))
                        for row in cursor.fetchall()]

            err = False
            for res in result:
                for count in range(1, 13):
                    if (res['sm'+str(count)]) < 0:
                        err = True

            if (err):
                transaction.set_rollback(True)
                return HttpResponse('{"status": "Ошибка сохранения документа. Проверьте введенные суммы!"}', content_type="application/json", status=400)

            return HttpResponse('{"status": "Документ успешно сохранен №' + str(itemdoc.nom) + '"}', content_type="application/json", status=200)
    except Exception as e:
        response_data = {
            "status": e.args[0]
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def izmincdelete(request, id):
    try:
        docobj = izm_inc.objects.get(id=id)
        # docobj.deleted = not docobj.deleted
        docobj.delete()

        # табличная часть
        tbl1objs = izm_inc_tbl1.objects.filter(_izm_inc_id=id)
        for itmtbl1 in tbl1objs:
            # itmtbl1.deleted = docobj.deleted
            itmtbl1.delete()
    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status=400)

    queryset = izm_inc.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_inc_Serializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


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

    # Получаем остатки сумм плана (фильры по организации - обязательно, дата, классификация)
    data = getincplanbyclassif(_organization, date=date,
                              _classification_id=_classification)
    if len(data)>0:
        res = data[0]

    obj =  {
		"id": 0,
		"_classification": {
			"id": res['_classification'],
			"name_kaz": res['classification_name'],
			"name_rus": res['classification_name'],
			"code": res['classification_code']
		},
		"_date": "","deleted": False,"utvgod": 0,"god": 0,"itoggod": 0    
    }

    for ind in range(1, 13):
        obj["utv" + str(ind)] = res["utv" + str(ind)]
        obj["sm" + str(ind)] = res["sm" + str(ind)]
        obj["itog" + str(ind)] = res["itog" + str(ind)]

    return HttpResponse(json.dumps(obj), content_type="application/json")


# ****************************************************************
# ***Сервисы утвержденного плана финансирования по расходам***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvexplist(request):
    queryset = utv_exp.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_exp_Serializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvexpitem(request, id):

    if (id==0):
        try:
            org = profile.objects.get(_user_id = request.user.pk)._organization
        except:
            response_data = {"status": "Не указана текущая организация в профиле пользователя"}
            return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)

        resp = {
                    "doc": {
                        "id": 0,
                        "_organization": {
                            "id": org.id,
                            "name_rus": org.name_rus,
                            "name_kaz":org.name_kaz
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

    # табличная часть платежи
    queryset_paym = utv_exp_pay.objects.filter(_utv_exp_id=queryset_doc.id)
    serial_paym = utv_exp_paymentserial(queryset_paym, many=True)

    # табличная часть платежи
    queryset_oblig = utv_exp_obl.objects.filter(_utv_exp_id=queryset_doc.id)
    serial_oblig = utv_exp_obligatserial(queryset_oblig, many=True)

    # Возвращаем шапку и табличную часть в одном объекте
    resp = {'doc': serialdoc.data,
            'payments': serial_paym.data,
            'obligats': serial_oblig.data,
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
            sm = itemtbl1['sm' +
                str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
            if sm < 0:
                return HttpResponse('{"status": "Сумма в утвержденном плане не должна быть меньше 0"}', content_type="application/json", status=400)

    for itemtbl1 in obligs:
        for ind in range(1, 13):
            sm = itemtbl1['sm' +
                str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
            if sm < 0:
                return HttpResponse('{"status": "Сумма в утвержденном плане не должна быть меньше 0"}', content_type="application/json", status=400)


    try:
        with transaction.atomic():
            # Начало записи шапки документа--------------------------------------
            doc_id = doc_req['id']
            org = organization.objects.get(id=doc_req['_organization']['id'])
            budjet_id = org._budjet.id
            date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')   
        

            if doc_req['id'] == 0:
                year = date_object.year
                doc_list = utv_exp.objects.filter(
                    _date__year=year, _organization=org.id)
                correct = True
                for itemdoc in doc_list:
                    if not itemdoc.deleted:
                        correct = False

                if not correct:
                    transaction.set_rollback(True)
                    return HttpResponse('{"status": "Утвержденный план на этот год уже имеется. Удалите предыдущий документ!"}', content_type="application/json", status=400)

                itemdoc = utv_exp()
                itemdoc.nom = str(doc_list.count() + 1) + '-' + org.bin
            else:
                itemdoc = utv_exp.objects.get(id=doc_id)

            itemdoc._organization_id = org.id
            itemdoc._budjet_id = budjet_id
            itemdoc._date = date_object
            itemdoc.save()
            # -----------конец записи шапки документа-----------------------------


            # Начало записи табличных частей документа
            #Очищаем предыдущие записи табличной части
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
                if (itemtbl1['_fkr']['id']==0):
                    continue

                newitemtbl1 = utv_exp_pay()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                newitemtbl1.god = itemtbl1['god']
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
                newregrec.god = itemtbl1['god']
                god = 0
                for ind in range(1, 13):
                    sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
                    god += sm
                    setattr(newregrec, 'sm' + str(ind), sm)
                newregrec.god = god
                reg_exp_pay_list.append(newregrec)


            for itemtbl1 in obligs:
                if (itemtbl1['_fkr']['id']==0):
                    continue
                newitemtbl1 = utv_exp_obl()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                newitemtbl1.god = itemtbl1['god']
                for ind in range(1, 13):
                    sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
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
                    sm = itemtbl1['sm' + str(ind)] if not itemtbl1['sm' + str(ind)] == None else 0
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
                transaction.set_rollback(True, "Суммы платежей и обязательства не совпадают")

            return HttpResponse('{"status": "Успешно записан документ"}', content_type="application/json")

    except Exception as e:
        response_data = {
            "status": e.args[0]
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json", status = 400)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def utvexpdelete(request, id):
    try:
        docobj = utv_exp.objects.get(id = id)
        docobj.deleted = not docobj.deleted
        

        # табличная часть
        payms = utv_exp_pay.objects.filter(_utv_exp_id=docobj.id)
        for itmtbl1 in payms:
            # itmtbl1.deleted = docobj.deleted
            itmtbl1.delete()

        # табличная часть
        obligs = utv_exp_obl.objects.filter(_utv_exp_id=docobj.id)
        for itmtbl1 in obligs:
            # itmtbl1.deleted = docobj.deleted
            itmtbl1.delete()

        docobj.delete()
    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status = 400)

    queryset = utv_exp.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_exp_Serializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)





# ****************************************************************
# ***Сервисы изменения плана***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmexplist(request):
    queryset = izm_exp.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_exp_serial(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmexpitem(request, id_doc):
    try:
        org = profile.objects.get(_user_id = request.user.pk)._organization
    except:
        response_data = {"status": "Не указана текущая организация в профиле пользователя"}
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

    if (id_doc==0):
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

    if len(result)==0:
        response_data = {"status": "Ошибка, не найден выбранный документ в базе"}
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
    

    try:
        org = organization.objects.get(id=doc_req['_organization']['id'])
        budjet_id = org._budjet.id
        date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
        year = date_object.year
        month = date_object.month


        # Начало транзации записи документа
        with transaction.atomic():
            if doc_req['id'] == 0:
                doc_cnt = izm_exp.objects.filter(_date__year = year, _organization = org.id).count()
                itemdoc = izm_exp()      
                itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            else:
                itemdoc = izm_exp.objects.get(id = doc_req['id'])
            itemdoc._organization_id = org.id
            itemdoc._budjet_id = budjet_id        
            itemdoc._date = date_object   
            if doc_req['_type_izm_doc']['id']==0:
                itemdoc._type_izm_doc_id = 1
            else:
                itemdoc._type_izm_doc_id = doc_req['_type_izm_doc']['id']
            itemdoc.save()


            #Очищаем предыдущие записи табличной части
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
                        transaction.set_rollback(True)
                        return HttpResponse(json.dumps({"status":"Нельзя редактировать предыдущие месяцы"}), content_type="application/json", status=400)
            
                    if (month < ind) and ((utv + sm) < 0):
                        transaction.set_rollback(True)
                        return HttpResponse(json.dumps({"status":"Нельзя в будущих месяцах указывать сумму больше остатка!"}), content_type="application/json", status=400)

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
                    if (month==ind) and ((utv + sm) < 0):
                        ost = -sm
                        j = ind
                        while ost > 0 and j>0:
                            utv_new = itemtbl1['utv' + str(j)] if not itemtbl1['utv' + str(j)] == None else 0
                            sum = min(utv_new, ost)
                            setattr(newregrec, 'sm' + str(j), -sum)
                            god += (-sum)
                            ost -= sum
                            j -= 1
                        
                        if ost > 0:
                            transaction.set_rollback(True, "Не хватает сумм в платежах. Проверьте суммы.")
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
                    if (month==ind) and ((utv + sm) < 0):
                        ost = -sm
                        j = ind
                        while ost > 0 and j>0:
                            utv_new = itemtbl1['utv' + str(j)] if not itemtbl1['utv' + str(j)] == None else 0
                            sum = min(utv_new, ost)
                            setattr(newregrec, 'sm' + str(j), -sum)
                            god += (-sum)
                            ost -= sum
                            j -= 1
                        
                        if ost > 0:
                            transaction.set_rollback(True, "Не хватает сумм в обязательствах. Проверьте суммы.")
                        break
                    else:
                        god += sm
                newregrec.god = god
                reg_exp_obl_list.append(newregrec)


            izm_exp_obl.objects.bulk_create(izm_exp_obl_list)
            reg_exp_obl.objects.bulk_create(reg_exp_obl_list)









            #***********************************************************************************
            #**********ПРОВЕРКА ОСТАТКОВ ПОСЛЕ ЗАПИСИ ДОКУМЕНТА. *******************************
            #***********************************************************************************
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
                                ORDER BY _fkr_id, _spec_id   
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
                if not res_obl[i]["god"] == res_pay[i]["god"]:
                    transaction.set_rollback(True)
                    return HttpResponse(json.dumps({"status": "Сумма обязательства и платежей не совпадают"}), content_type="application/json", status=400)

                for j in range(1, 13):
                    if res_obl[i]["sm" + str(j)] < res_pay[i]["sm" + str(j)]:
                        errormess = errormess  + res_obl[i]["fkr_code"] + " - " + res_obl[i]["spec_code"] + " превышение! \n"
                        break

            if not errormess=="":
                transaction.set_rollback(True)
                return HttpResponse(json.dumps({"status": errormess}), content_type="application/json", status=400)

            return HttpResponse(json.dumps({"status": "Документ успешно записан"}), content_type="application/json", status=200)

    except Exception as e:
        response_data = {
            "status": e.args[0]
        }
        return HttpResponse(json.dumps(response_data), content_type="application/json", status=400)
          


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def izmexpdelete(request, id):
    try:
        # табличная часть
        payms = izm_exp_pay.objects.filter(_izm_exp_id=id)
        for itmtbl1 in payms:
            # itmtbl1.deleted = docobj.deleted
            itmtbl1.delete()

        docobj = izm_exp.objects.get(id = id)
        # docobj.deleted = not docobj.deleted
        docobj.delete()

        

    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status = 400)

    queryset = izm_exp.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_exp_serial(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def expgetplanbyclassif(request):
    datastr = request.body
    data = json.loads(datastr)
    table = data['table']
    _organization = data['_organization']
    _fkr = data['_fkr']
    _spec = data['_spec']
    _date = data['_date']
    date = datetime.strptime(_date, "%d.%m.%Y %H:%M:%S")

    qset_fkr = fkr.objects.get(id=_fkr)
    qset_spec = spec_exp.objects.get(id=_spec)
    
    resp = {
        "_fkr_id":qset_fkr.id,
        "_fkr_name":qset_fkr.name_rus,
        "_fkr_code":qset_fkr.code,
        "_spec_id":qset_spec.id,
        "_spec_name":qset_spec.name_rus,
        "_spec_code":qset_spec.code
    }


    query = f"""with union_utv_izm as (SELECT _fkr_id, _spec_id, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12 
                            FROM public.docs_reg_exp_{table}
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
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        result = [dict(zip(columns, row))
                for row in cursor.fetchall()]
    if len(result)>0:
        merged_dict = {**resp, **result[0]}
        merged_json = json.dumps(merged_dict)
    else:
        for ind in range(1, 13):
            resp["utv" + str(ind)] = 0
            resp["sm" + str(ind)] = 0
            resp["itog" + str(ind)] = 0
        merged_json = json.dumps(resp)


    return HttpResponse(merged_json, content_type="application/json")












# ****************************************************************
# *****Сервисы импорт по поступлениям 2-19*****
# ****************************************************************
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_219(request):
    jsreq = json.loads(request.body)
    filesname = jsreq['file']

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
                newdoc._organization_id = 1
                newdoc.save()

                bulk_mass = []
                for item in mass_obj:
                    newzap = import219_tbl1()
                    newzap._import219_id = newdoc.id
                    newzap._date = date
                    newzap._budjet_id = _budjet_id
                    newzap._organization_id = 1

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
    queryset = import219.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = import_serial(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import219item(request, id_doc):
    queryset = type_izm_doc.objects.all()
    serialtype = typedocSerializer(queryset, many=True)

    qset = import219.objects.get(id = id_doc)
    serial = import_serial(qset, many = False)

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




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_420(request):
    pdffileobj = open("imports/420/2501.pdf", 'rb')
    pdfreader = PdfReader(pdffileobj)

    x = len(pdfreader.pages)

    abp = ""
    bp = ""
    podpr = ""
    spec = ""
    itogsums = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]

    for num in range(0, x):
        pageobj = pdfreader.pages[num]
        text = pageobj.extract_text().split('\n')

        if not text[0] == 'Форма № 4-20':
            return "not 2-19 file"

        

        for i in range(len(text)):
            sums = [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]

            if i >= 15 and num==0:
                count = 0
                prostotext = False
                str = text[i]

                for char in str:
                    if char.isspace():
                        count += 1
                    else:
                        if (char in ('1234567890')):
                            break
                        else:
                            prostotext = True
                            break

                if prostotext:
                    continue

                if (count == 0):
                    abp = ""
                elif (count == 3):
                    bp = ""
                elif (count == 7):
                    podpr = ""
                elif (count == 12):
                    spec = ""

                # ищем АБП
                if abp == "":
                    abp = text[i].split(' ')[0]

                # ищем БП
                elif not abp == "" and bp == "":
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

                    print(abp + '/' + bp + '/' +    podpr + '/' + spec + '      ', sums)
        
    print(itogsums)

    return HttpResponse('{"status": "данные успешно записаны"}', content_type="application/json", status = 200)




