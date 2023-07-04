from django.http import HttpResponse
from rest_framework import pagination, response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json
import base64
from datetime import datetime
from django.db import connection
from .models import *
from .serializer import *
# Общий модуль импортируем
from .shareModuleInc import *
from asgiref.sync import async_to_sync


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
    serial = utv_inc_Serializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvincitem(request, id):
    # Документ сам (шапка документа)
    queryset_doc = utv_inc.objects.get(id=id)
    serialdoc = utv_inc_Serializer(queryset_doc)

    # табличная часть
    queryset_tbl1 = utv_inc_tbl1.objects.filter(_utv_inc_id=queryset_doc.id)
    serial_tbl1 = utv_inc_tbl1_Serializer(queryset_tbl1, many = True)

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

    try:
        if doc_req['id'] == None:
            date_object = datetime.strptime(doc_req['_date'], '%Y-%m-%d')
            year = date_object.year
            org = organization.objects.get(id=doc_req['_organization'])
            doc_cnt = utv_inc.objects.filter(date__year = year).count()
            itemdoc = utv_inc()
            itemdoc._organization_id = doc_req['_organization']
            itemdoc._budjet_id = org._budjet.id
            itemdoc._date = doc_req['_date']
            itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            itemdoc.save()
        else:
            org = organization.objects.get(id=doc_req['_organization'])
            itemdoc = utv_inc.objects.get(id = doc_req['id'])
            itemdoc._organization_id = doc_req['_organization']
            itemdoc._budjet_id = org._budjet.id
            itemdoc._date = datetime.strptime(doc_req['_date'],"%d.%m.%Y")
            # itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            itemdoc.save()
    except:
        return HttpResponse('{"status": "Ошибка в шапке документа"}', content_type="application/json", status = 400)

    try:
        mass_id_tbl = []
        if doc_req['id'] == None:
            for itemtbl1 in tbl1_req:
                newitemtbl1 = utv_inc_tbl1()
                newitemtbl1._utv_inc_id = itemdoc.id
                newitemtbl1._classification_id = itemtbl1['_classification']
                newitemtbl1._organization_id = doc_req['_organization']
                newitemtbl1._date = doc_req['_date']
                newitemtbl1.god = itemtbl1['god']
                newitemtbl1.sm1 = itemtbl1['sm1']
                newitemtbl1.sm2 = itemtbl1['sm2']
                newitemtbl1.sm3 = itemtbl1['sm3']
                newitemtbl1.sm4 = itemtbl1['sm4']
                newitemtbl1.sm5 = itemtbl1['sm5']
                newitemtbl1.sm6 = itemtbl1['sm6']
                newitemtbl1.sm7 = itemtbl1['sm7']
                newitemtbl1.sm8 = itemtbl1['sm8']
                newitemtbl1.sm9 = itemtbl1['sm9']
                newitemtbl1.sm10 = itemtbl1['sm10']
                newitemtbl1.sm11 = itemtbl1['sm11']
                newitemtbl1.sm12 = itemtbl1['sm12']
                newitemtbl1.save()
                mass_id_tbl.append(newitemtbl1.id)
        else:
            for itemtbl1 in tbl1_req:
                if itemtbl1['id'] == 0:
                    newitemtbl1 = utv_inc_tbl1()
                else:
                    newitemtbl1 = utv_inc_tbl1.objects.get(id = itemtbl1['id'])

                newitemtbl1._utv_inc_id = itemdoc.id
                newitemtbl1._classification_id = itemtbl1['_classification']
                newitemtbl1._organization_id = doc_req['_organization']
                newitemtbl1._date = datetime.strptime(doc_req['_date'],"%d.%m.%Y")
                newitemtbl1.god = itemtbl1['god']
                newitemtbl1.sm1 = itemtbl1['sm1']
                newitemtbl1.sm2 = itemtbl1['sm2']
                newitemtbl1.sm3 = itemtbl1['sm3']
                newitemtbl1.sm4 = itemtbl1['sm4']
                newitemtbl1.sm5 = itemtbl1['sm5']
                newitemtbl1.sm6 = itemtbl1['sm6']
                newitemtbl1.sm7 = itemtbl1['sm7']
                newitemtbl1.sm8 = itemtbl1['sm8']
                newitemtbl1.sm9 = itemtbl1['sm9']
                newitemtbl1.sm10 = itemtbl1['sm10']
                newitemtbl1.sm11 = itemtbl1['sm11']
                newitemtbl1.sm12 = itemtbl1['sm12']
                newitemtbl1.save()
                mass_id_tbl.append(newitemtbl1.id)

        #Удаляем удаленные с фронта элементы табл части документа
        newitemtbl1 = utv_inc_tbl1.objects.filter(_utv_inc_id = itemdoc.id)
        for itemtblbs in newitemtbl1:
            if not itemtblbs.id in mass_id_tbl:
                itemtblbs.delete()

    except:
        return HttpResponse('{"status": "Ошибка в табличной части документа"}', content_type="application/json", status = 400)


    # Документ сам (шапка документа)
    queryset_doc = utv_inc.objects.get(id=itemdoc.id)
    serialdoc = utv_inc_Serializer(queryset_doc)

    # табличная часть
    queryset_tbl1 = utv_inc_tbl1.objects.filter(_utv_inc_id=queryset_doc.id)
    serial_tbl1 = utv_inc_tbl1_Serializer(queryset_tbl1, many = True)

    # Возвращаем шапку и табличную часть в одном объекте
    resp = {'doc': serialdoc.data,
            'tbl1': serial_tbl1.data}

    return response.Response(resp)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def utvincdelete(request, id):
    try:
        docobj = utv_inc.objects.get(id = id)
        docobj.deleted = not docobj.deleted
        docobj.save()

        # табличная часть
        tbl1objs = utv_inc_tbl1.objects.filter(_utv_inc_id=docobj.id)
        for itmtbl1 in tbl1objs:
            itmtbl1.deleted = not itmtbl1.deleted
            itmtbl1.save()
    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status = 400)

    queryset = utv_inc.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_inc_Serializer(paginated_queryset, many = True)
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
    serial = izm_inc_Serializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmincitem(request, id):
    # Документ сам (шапка документа)
    queryset_doc = izm_inc.objects.get(id=id)
    serialdoc = izm_inc_Serializer(queryset_doc)

    queryset_tbl1 = izm_inc_tbl1.objects.filter(_izm_inc_id=queryset_doc.id).order_by('_classification')
    serialtbl1 = izm_inc_tbl1_Serializer(queryset_tbl1, many = True)

    resp = {
            'doc': serialdoc.data,
            'tbl1': serialtbl1.data
            }
    tbl1res = json.dumps(resp)
    return HttpResponse(tbl1res, content_type="application/json", status = 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def izmincsave(request):
    datastr = request.body
    data = json.loads(datastr)
    doc_req = data['doc']
    tbl1_req = data['tbl1']


    list_clasif = ''
    for itm in tbl1_req:
        if list_clasif == '':
            list_clasif = str(itm['_classification'])
            continue
        list_clasif = list_clasif  + ', ' + str(itm['_classification']) 

    date = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
    date_start = datetime.strptime(str(date.year) + "-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
    dateend = date

    query = f"""with sm as (SELECT _classification_id, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12 
                                FROM public.docs_utv_inc_tbl1
                                where _organization_id = {doc_req['_organization']} and not deleted and _date>='{date_start}' and _date < '{dateend}' and _classification_id in ({list_clasif})  
                                group by _classification_id),
                        izm as (SELECT _classification_id,  sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12 
                                FROM public.docs_izm_inc_tbl1
                                where _organization_id = {doc_req['_organization']} and not deleted and _date>='{date_start}' and _date < '{dateend}' and _classification_id in ({list_clasif})
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
        

    masserror = []
    # Фрагмент проверки сумм изменении и остатков
    for itm in tbl1_req:
        ost = [itemres for itemres in result if itemres['_classification'] == itm['_classification']]
        if len(ost)==0:
            return HttpResponse('{"status": "Ошибка в строке с классификацией ' + itm['classification_name'] + '"}', content_type="application/json", status = 400)
        
        for count in range(1, 13):
            if (itm['sm'+str(count)] + ost[0]['sm'+str(count)]) < 0:
                masserror.append({"_classification": itm['_classification'],  "month":count, "name":itm['classification_name'], "code":itm['classification_code']})


    # Если массив не пустой, то возвращаем ошибку с описанием
    if len(masserror)>0:
        return HttpResponse('{"status": "Нет остатков сумм по ' + masserror[0]['code'] + "  " + masserror[0]['name'] + '"}', content_type="application/json", status = 400)
                    
    # Запис шапки документа изменения по поступлениям
    try:
        date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')
        org = organization.objects.get(id=doc_req['_organization'])
        
        # Если ИД=0, то создаем новый документ поступления
        if doc_req['id'] == 0:
            itemdoc = izm_inc()
            year = date_object.year
            doc_cnt = izm_inc.objects.filter(_date__year = year).count()
            itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
        # Иначе получаем уже имеющиеся документ
        else:
            itemdoc = izm_inc.objects.get(id=doc_req['id'])

        itemdoc._organization_id = doc_req['_organization']
        itemdoc._type_izm_doc_id = doc_req['_type_izm_doc']
        itemdoc._budjet_id = org._budjet.id
        itemdoc._date = date_object
        # Непосредственно сохранение документа
        itemdoc.save()
    except:
        return HttpResponse('{"status": "Ошибка в шапке документа"}', content_type="application/json", status = 400)

    # Запись табличной части документа изменения по поступлениям
    try:
        ids_tbl1 = []
        for itemtbl1 in tbl1_req:
            if itemtbl1['id'] == 0:
                # если ид = 0. то создаем новый
                newitemtbl1 = izm_inc_tbl1()
            else:
                # иначе получаем существующий документ
                newitemtbl1 = izm_inc_tbl1.objects.get(id=itemtbl1['id'])

            newitemtbl1._izm_inc_id = itemdoc.id
            newitemtbl1._classification_id = itemtbl1['_classification']
            newitemtbl1._organization_id = doc_req['_organization']
            newitemtbl1._date = date_object

            newitemtbl1.utv1 = itemtbl1['utv1'] if not itemtbl1['utv1']==None else 0
            newitemtbl1.utv2 = itemtbl1['utv2'] if not itemtbl1['utv2']==None else 0
            newitemtbl1.utv3 = itemtbl1['utv3'] if not itemtbl1['utv3']==None else 0
            newitemtbl1.utv4 = itemtbl1['utv4'] if not itemtbl1['utv4']==None else 0
            newitemtbl1.utv5 = itemtbl1['utv5'] if not itemtbl1['utv5']==None else 0
            newitemtbl1.utv6 = itemtbl1['utv6'] if not itemtbl1['utv6']==None else 0
            newitemtbl1.utv7 = itemtbl1['utv7'] if not itemtbl1['utv7']==None else 0
            newitemtbl1.utv8 = itemtbl1['utv8'] if not itemtbl1['utv8']==None else 0
            newitemtbl1.utv9 = itemtbl1['utv9'] if not itemtbl1['utv9']==None else 0
            newitemtbl1.utv10 = itemtbl1['utv10'] if not itemtbl1['utv10']==None else 0
            newitemtbl1.utv11= itemtbl1['utv11'] if not itemtbl1['utv11']==None else 0
            newitemtbl1.utv12 = itemtbl1['utv12'] if not itemtbl1['utv12']==None else 0

            newitemtbl1.sm1 = itemtbl1['sm1'] if not itemtbl1['sm1']==None else 0
            newitemtbl1.sm2 = itemtbl1['sm2'] if not itemtbl1['sm2']==None else 0
            newitemtbl1.sm3 = itemtbl1['sm3'] if not itemtbl1['sm3']==None else 0
            newitemtbl1.sm4 = itemtbl1['sm4'] if not itemtbl1['sm4']==None else 0
            newitemtbl1.sm5 = itemtbl1['sm5'] if not itemtbl1['sm5']==None else 0
            newitemtbl1.sm6 = itemtbl1['sm6'] if not itemtbl1['sm6']==None else 0
            newitemtbl1.sm7 = itemtbl1['sm7'] if not itemtbl1['sm7']==None else 0
            newitemtbl1.sm8 = itemtbl1['sm8'] if not itemtbl1['sm8']==None else 0
            newitemtbl1.sm9 = itemtbl1['sm9'] if not itemtbl1['sm9']==None else 0
            newitemtbl1.sm10 = itemtbl1['sm10'] if not itemtbl1['sm10']==None else 0
            newitemtbl1.sm11 = itemtbl1['sm11'] if not itemtbl1['sm11']==None else 0
            newitemtbl1.sm12 = itemtbl1['sm12'] if not itemtbl1['sm12']==None else 0

            newitemtbl1.itog1 = itemtbl1['itog1'] if not itemtbl1['itog1']==None else 0
            newitemtbl1.itog2 = itemtbl1['itog2'] if not itemtbl1['itog2']==None else 0
            newitemtbl1.itog3 = itemtbl1['itog3'] if not itemtbl1['itog3']==None else 0
            newitemtbl1.itog4 = itemtbl1['itog4'] if not itemtbl1['itog4']==None else 0
            newitemtbl1.itog5 = itemtbl1['itog5'] if not itemtbl1['itog5']==None else 0
            newitemtbl1.itog6 = itemtbl1['itog6'] if not itemtbl1['itog6']==None else 0
            newitemtbl1.itog7 = itemtbl1['itog7'] if not itemtbl1['itog7']==None else 0
            newitemtbl1.itog8 = itemtbl1['itog8'] if not itemtbl1['itog8']==None else 0
            newitemtbl1.itog9 = itemtbl1['itog9'] if not itemtbl1['itog9']==None else 0
            newitemtbl1.itog10 = itemtbl1['itog10'] if not itemtbl1['itog10']==None else 0
            newitemtbl1.itog11 = itemtbl1['itog11'] if not itemtbl1['itog11']==None else 0
            newitemtbl1.itog12 = itemtbl1['itog12'] if not itemtbl1['itog12']==None else 0

            newitemtbl1.save()
            ids_tbl1.append(newitemtbl1.id)

            
        
        # Удаление не существующих строк в БД
        deleteitem = izm_inc_tbl1.objects.filter(_izm_inc = doc_req['id']).exclude(id__in = ids_tbl1)
        for itmdel in deleteitem:
            itmdel.delete()
    except:
        return HttpResponse('{"status": "Ошибка в табличной части документа"}', content_type="application/json", status = 400)


    return HttpResponse('{"status": "Документ успешно сохранен №'+ str(itemdoc.nom) +'"}', content_type="application/json", status = 200) 


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def izmincdelete(request, id):
    try:
        docobj = izm_inc.objects.get(id = id)
        docobj.deleted = not docobj.deleted
        docobj.save()

        # табличная часть
        tbl1objs = izm_inc_tbl1.objects.filter(_izm_inc_id=docobj.id)
        for itmtbl1 in tbl1objs:
            itmtbl1.deleted = docobj.deleted
            itmtbl1.save()
    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status = 400)

    queryset = izm_inc.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_inc_Serializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def incgetplanbyclassif(request):
    _organization = request.GET.get("_organization")
    _classification = request.GET.get("_classification")
    strdate = request.GET.get("date")

    if _organization == None:
        return HttpResponse('{"status": "Ошибка получения данных"}', content_type="application/json", status = 400)

    date = None
    if not strdate == None:
        date = datetime.strptime(strdate,"%d.%m.%Y %H:%M:%S").date()
    
    # Получаем остатки сумм плана (фильры по организации - обязательно, дата, классификация)
    res = getincplanbyclassif(_organization, date = date, classification = _classification)

     # табличная часть
    # mass = []
    # for itm in res:
    #     mass.append({ "tip":"utv", "id":0, "_classification":itm['_classification_id'], "classification_name":itm['classification_name'], "sm1":itm['sm1'], "sm2":itm['sm2'], "sm3":itm['sm3'], "sm4":itm['sm5'], "sm5":itm['sm5'], "sm6":itm['sm6'], "sm7":itm['sm7'], "sm8":itm['sm8'], "sm9":itm['sm9'], "sm10":itm['sm10'], "sm11":itm['sm11'], "sm12":itm['sm12']})
    #     mass.append({ 'tip':'sm', "id":0, '_classification':itm['_classification_id'], "classification_name":itm['classification_name'],'sm1':0, 'sm2':0, 'sm3':0, 'sm4':0, 'sm5':0, "sm6":0, "sm7":0, "sm8":0, "sm9":0, "sm10":0, "sm11":0, "sm12":0})
    #     mass.append({ 'tip':'itog', "id":0, '_classification':itm['_classification_id'], "classification_name":itm['classification_name'],'sm1':0, 'sm2':0, 'sm3':0, 'sm4':0, 'sm5':0, "sm6":0, "sm7":0, "sm8":0, "sm9":0, "sm10":0, "sm11":0, "sm12":0 })
    return HttpResponse(json.dumps(res), content_type="application/json")






# ****************************************************************
# ***Сервисы утвержденного плана финансирования по расходам***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvexplist(request):
    queryset = utv_exp.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_exp_Serializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def utvexpitem(request, id):
    # Документ сам (шапка документа)
    queryset_doc = utv_exp.objects.get(id=id)
    serialdoc = utv_exp_Serializer(queryset_doc)

    # табличная часть платежи
    queryset_paym = utv_exp_paym.objects.filter(_utv_exp_id=queryset_doc.id)
    serial_paym = utv_exp_paymentserial(queryset_paym, many = True)

    # табличная часть платежи
    queryset_oblig = utv_exp_oblig.objects.filter(_utv_exp_id=queryset_doc.id)
    serial_oblig = utv_exp_obligatserial(queryset_oblig, many = True)

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

    try:
        org = organization.objects.get(id=doc_req['_organization']['id'])
        budjet_id = org._budjet.id
        date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')

        if doc_req['id'] == 0:
            year = date_object.year
            doc_cnt = utv_exp.objects.filter(_date__year = year, _organization = org.id).count()
            itemdoc = utv_exp()
            itemdoc._organization_id = org.id
            itemdoc._budjet_id = budjet_id
            itemdoc._date = date_object
            itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            itemdoc.save()
        else:
            itemdoc = utv_exp.objects.get(id = doc_req['id'])
            itemdoc._organization_id = org.id
            itemdoc._budjet_id = budjet_id
            itemdoc._date = date_object
            itemdoc.save()
    except:
        return HttpResponse('{"status": "Ошибка в шапке документа"}', content_type="application/json", status = 400)

    if 1 == 1:
        mass_id_paym = []
        mass_id_oblig = []

        if doc_req['id'] == 0:
            for itemtbl1 in payments:
                newitemtbl1 = utv_exp_paym()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                # newitemtbl1.god = itemtbl1['god']
                newitemtbl1.sm1 = itemtbl1['sm1']
                newitemtbl1.sm2 = itemtbl1['sm2']
                newitemtbl1.sm3 = itemtbl1['sm3']
                newitemtbl1.sm4 = itemtbl1['sm4']
                newitemtbl1.sm5 = itemtbl1['sm5']
                newitemtbl1.sm6 = itemtbl1['sm6']
                newitemtbl1.sm7 = itemtbl1['sm7']
                newitemtbl1.sm8 = itemtbl1['sm8']
                newitemtbl1.sm9 = itemtbl1['sm9']
                newitemtbl1.sm10 = itemtbl1['sm10']
                newitemtbl1.sm11 = itemtbl1['sm11']
                newitemtbl1.sm12 = itemtbl1['sm12']
                newitemtbl1.save()
                mass_id_paym.append(newitemtbl1.id)

            for itemtbl1 in obligs:
                newitemtbl1 = utv_exp_oblig()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                # newitemtbl1.god = itemtbl1['god']
                newitemtbl1.sm1 = itemtbl1['sm1']
                newitemtbl1.sm2 = itemtbl1['sm2']
                newitemtbl1.sm3 = itemtbl1['sm3']
                newitemtbl1.sm4 = itemtbl1['sm4']
                newitemtbl1.sm5 = itemtbl1['sm5']
                newitemtbl1.sm6 = itemtbl1['sm6']
                newitemtbl1.sm7 = itemtbl1['sm7']
                newitemtbl1.sm8 = itemtbl1['sm8']
                newitemtbl1.sm9 = itemtbl1['sm9']
                newitemtbl1.sm10 = itemtbl1['sm10']
                newitemtbl1.sm11 = itemtbl1['sm11']
                newitemtbl1.sm12 = itemtbl1['sm12']
                newitemtbl1.save()
                mass_id_oblig.append(newitemtbl1.id)
        else:
            for itemtbl1 in payments:
                try: newitemtbl1 = utv_exp_paym.objects.get(id = itemtbl1['id'])
                except: newitemtbl1 = utv_exp_paym()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                # newitemtbl1.god = itemtbl1['god']
                newitemtbl1.sm1 = itemtbl1['sm1']
                newitemtbl1.sm2 = itemtbl1['sm2']
                newitemtbl1.sm3 = itemtbl1['sm3']
                newitemtbl1.sm4 = itemtbl1['sm4']
                newitemtbl1.sm5 = itemtbl1['sm5']
                newitemtbl1.sm6 = itemtbl1['sm6']
                newitemtbl1.sm7 = itemtbl1['sm7']
                newitemtbl1.sm8 = itemtbl1['sm8']
                newitemtbl1.sm9 = itemtbl1['sm9']
                newitemtbl1.sm10 = itemtbl1['sm10']
                newitemtbl1.sm11 = itemtbl1['sm11']
                newitemtbl1.sm12 = itemtbl1['sm12']
                newitemtbl1.save()
                mass_id_paym.append(newitemtbl1.id)

            for itemtbl1 in obligs:
                try: newitemtbl1 = utv_exp_oblig.objects.get(id = itemtbl1['id'])
                except: newitemtbl1 = utv_exp_oblig()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                # newitemtbl1.god = itemtbl1['god']
                newitemtbl1.sm1 = itemtbl1['sm1']
                newitemtbl1.sm2 = itemtbl1['sm2']
                newitemtbl1.sm3 = itemtbl1['sm3']
                newitemtbl1.sm4 = itemtbl1['sm4']
                newitemtbl1.sm5 = itemtbl1['sm5']
                newitemtbl1.sm6 = itemtbl1['sm6']
                newitemtbl1.sm7 = itemtbl1['sm7']
                newitemtbl1.sm8 = itemtbl1['sm8']
                newitemtbl1.sm9 = itemtbl1['sm9']
                newitemtbl1.sm10 = itemtbl1['sm10']
                newitemtbl1.sm11 = itemtbl1['sm11']
                newitemtbl1.sm12 = itemtbl1['sm12']
                newitemtbl1.save()
                mass_id_oblig.append(newitemtbl1.id)

        #Удаляем удаленные с фронта элементы табл части документа
        allitems = utv_exp_paym.objects.filter(_utv_exp_id = itemdoc.id)
        for itemtblbs in allitems:
            if not itemtblbs.id in mass_id_paym:
                itemtblbs.delete()

        allitems = utv_exp_oblig.objects.filter(_utv_exp_id = itemdoc.id)
        for itemtblbs in allitems:
            if not itemtblbs.id in mass_id_paym:
                itemtblbs.delete()

    # except:
    #     return HttpResponse('{"status": "Ошибка в табличной части документа"}', content_type="application/json", status = 400)


    # Документ сам (шапка документа)
    queryset_doc = utv_exp.objects.get(id = itemdoc.id)
    serialdoc = utv_exp_Serializer(queryset_doc)

    # табличная часть платежи
    queryset_paym = utv_exp_paym.objects.filter(_utv_exp_id=itemdoc.id)
    serial_paym = utv_exp_paymentserial(queryset_paym, many = True)

    # табличная часть платежи
    queryset_oblig = utv_exp_oblig.objects.filter(_utv_exp_id=itemdoc.id)
    serial_oblig = utv_exp_obligatserial(queryset_oblig, many = True)

    # Возвращаем шапку и табличную часть в одном объекте
    resp = {'doc': serialdoc.data,
            'payments': serial_paym.data,
            'obligats': serial_oblig.data,
            }

    return response.Response(resp)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def utvexpdelete(request, id):
    try:
        docobj = utv_exp.objects.get(id = id)
        docobj.deleted = not docobj.deleted
        docobj.save()

        # табличная часть
        payms = utv_exp_paym.objects.filter(_utv_exp_id=docobj.id)
        for itmtbl1 in payms:
            itmtbl1.deleted = docobj.deleted
            itmtbl1.save()

        # табличная часть
        obligs = utv_exp_oblig.objects.filter(_utv_exp_id=docobj.id)
        for itmtbl1 in obligs:
            itmtbl1.deleted = docobj.deleted
            itmtbl1.save()
    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status = 400)

    queryset = utv_exp.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = utv_exp_Serializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)





# ****************************************************************
# ***Сервисы изменения плана по платежам***
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmexppaymlist(request):
    queryset = izm_exp_paym.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_exp_paym_Serializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def izmexppaymitem(request, id):
    # Документ сам (шапка документа)
    queryset_doc = izm_exp_paym.objects.get(id=id)
    serialdoc = izm_exp_paym_Serializer(queryset_doc)

    # табличная часть платежи
    queryset_paym = izm_exp_paym_tbl.objects.filter(_izm_exp_paym_id = queryset_doc.id)
    serial_paym = izm_exp_paym_tbl_serial(queryset_paym, many = True)

    # Возвращаем шапку и табличную часть в одном объекте
    resp = {'doc': serialdoc.data,
            'payments': serial_paym.data
            }
    return response.Response(resp)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def izmexppaymsave(request):
    datastr = request.body
    data = json.loads(datastr)
    doc_req = data['doc']
    payments = data['payments']
 
    try:
        org = organization.objects.get(id=doc_req['_organization']['id'])
        budjet_id = org._budjet.id
        date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y %H:%M:%S')

        if doc_req['id'] == 0:
            year = date_object.year
            doc_cnt = izm_exp_paym.objects.filter(_date__year = year, _organization = org.id).count()
            itemdoc = izm_exp_paym()
            itemdoc._organization_id = org.id
            itemdoc._budjet_id = budjet_id
            itemdoc._date = date_object
            itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            itemdoc._type_izm_doc_id = doc_req['_type_izm_doc']['_type_izm_doc']
            itemdoc.save()
        else:
            itemdoc = izm_exp_paym.objects.get(id = doc_req['id'])
            itemdoc._organization_id = org.id
            itemdoc._budjet_id = budjet_id
            itemdoc._date = date_object
            itemdoc._type_izm_doc_id = doc_req['_type_izm_doc']['_type_izm_doc']
            itemdoc.save()
    except:
        return HttpResponse('{"status": "Ошибка в шапке документа"}', content_type="application/json", status = 400)



    if 1 == 1:
        mass_id_paym = []
        if doc_req['id'] == 0:
            for itemtbl1 in payments:
                newitemtbl1 = izm_exp_paym_tbl()
                newitemtbl1._izm_exp_paym_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                # newitemtbl1.god = itemtbl1['god']

                newitemtbl1.utv1 = itemtbl1['utv1']
                newitemtbl1.utv2 = itemtbl1['utv2']
                newitemtbl1.utv3 = itemtbl1['utv3']
                newitemtbl1.utv4 = itemtbl1['utv4']
                newitemtbl1.utv5 = itemtbl1['utv5']
                newitemtbl1.utv6 = itemtbl1['utv6']
                newitemtbl1.utv7 = itemtbl1['utv7']
                newitemtbl1.utv8 = itemtbl1['utv8']
                newitemtbl1.utv9 = itemtbl1['utv9']
                newitemtbl1.utv10 = itemtbl1['utv10']
                newitemtbl1.utv11 = itemtbl1['utv11']
                newitemtbl1.utv12 = itemtbl1['utv12']

                newitemtbl1.sm1 = itemtbl1['sm1']
                newitemtbl1.sm2 = itemtbl1['sm2']
                newitemtbl1.sm3 = itemtbl1['sm3']
                newitemtbl1.sm4 = itemtbl1['sm4']
                newitemtbl1.sm5 = itemtbl1['sm5']
                newitemtbl1.sm6 = itemtbl1['sm6']
                newitemtbl1.sm7 = itemtbl1['sm7']
                newitemtbl1.sm8 = itemtbl1['sm8']
                newitemtbl1.sm9 = itemtbl1['sm9']
                newitemtbl1.sm10 = itemtbl1['sm10']
                newitemtbl1.sm11 = itemtbl1['sm11']
                newitemtbl1.sm12 = itemtbl1['sm12']
                newitemtbl1.save()
                mass_id_paym.append(newitemtbl1.id)
        else:
            for itemtbl1 in payments:
                try: newitemtbl1 = izm_exp_paym_tbl.objects.get(id = itemtbl1['id'])
                except: newitemtbl1 = izm_exp_paym_tbl()
                newitemtbl1._izm_exp_paym_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_fkr']['id']
                newitemtbl1._spec_id = itemtbl1['_spec']['id']
                newitemtbl1._organization_id = org.id
                newitemtbl1._date = date_object
                # newitemtbl1.god = itemtbl1['god']

                newitemtbl1.utv1 = itemtbl1['utv1']
                newitemtbl1.utv2 = itemtbl1['utv2']
                newitemtbl1.utv3 = itemtbl1['utv3']
                newitemtbl1.utv4 = itemtbl1['utv4']
                newitemtbl1.utv5 = itemtbl1['utv5']
                newitemtbl1.utv6 = itemtbl1['utv6']
                newitemtbl1.utv7 = itemtbl1['utv7']
                newitemtbl1.utv8 = itemtbl1['utv8']
                newitemtbl1.utv9 = itemtbl1['utv9']
                newitemtbl1.utv10 = itemtbl1['utv10']
                newitemtbl1.utv11 = itemtbl1['utv11']
                newitemtbl1.utv12 = itemtbl1['utv12']

                newitemtbl1.sm1 = itemtbl1['sm1']
                newitemtbl1.sm2 = itemtbl1['sm2']
                newitemtbl1.sm3 = itemtbl1['sm3']
                newitemtbl1.sm4 = itemtbl1['sm4']
                newitemtbl1.sm5 = itemtbl1['sm5']
                newitemtbl1.sm6 = itemtbl1['sm6']
                newitemtbl1.sm7 = itemtbl1['sm7']
                newitemtbl1.sm8 = itemtbl1['sm8']
                newitemtbl1.sm9 = itemtbl1['sm9']
                newitemtbl1.sm10 = itemtbl1['sm10']
                newitemtbl1.sm11 = itemtbl1['sm11']
                newitemtbl1.sm12 = itemtbl1['sm12']
                newitemtbl1.save()
                mass_id_paym.append(newitemtbl1.id)


        #Удаляем удаленные с фронта элементы табл части документа
        allitems = izm_exp_paym_tbl.objects.filter(_izm_exp_paym_id = itemdoc.id)
        for itemtblbs in allitems:
            if not itemtblbs.id in mass_id_paym:
                itemtblbs.delete()

    # except:
    #     return HttpResponse('{"status": "Ошибка в табличной части документа"}', content_type="application/json", status = 400)


    # Документ сам (шапка документа)
    queryset_doc = izm_exp_paym.objects.get(id = itemdoc.id)
    serialdoc = izm_exp_paym_Serializer(queryset_doc)

    # табличная часть платежи
    queryset_paym = izm_exp_paym_tbl.objects.filter(_izm_exp_paym_id=itemdoc.id)
    serial_paym = izm_exp_paym_tbl_serial(queryset_paym, many = True)

    # Возвращаем шапку и табличную часть в одном объекте
    resp = {'doc': serialdoc.data,
            'payments': serial_paym.data
            }

    return response.Response(resp)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def izmexppaymdelete(request, id):
    try:
        docobj = izm_exp_paym.objects.get(id = id)
        docobj.deleted = not docobj.deleted
        docobj.save()

        # табличная часть
        payms = izm_exp_paym_tbl.objects.filter(_izm_exp_paym_id=docobj.id)
        for itmtbl1 in payms:
            itmtbl1.deleted = docobj.deleted
            itmtbl1.save()

    except:
        return HttpResponse('{"status": "Ошибка удаления документа"}', content_type="application/json", status = 400)

    queryset = izm_exp_paym.objects.order_by('nom')
    paginator = CustomPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serial = izm_exp_paym_Serializer(paginated_queryset, many = True)
    return paginator.get_paginated_response(serial.data)














# ****************************************************************
# *****Сервисы импорт по поступлениям 2-19*****
# ****************************************************************
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import219(request):
    jsreq = json.loads(request.body)
    with open("test.pdf", "wb") as f:
        strbs64 = jsreq['file']
        strbs64 = strbs64.split(',')[1]
        f.write(base64.b64decode(strbs64))
    pdftotext("test.pdf")
    return HttpResponse('{"status": "Ошибка получения данных"}', content_type="application/json", status = 200)






