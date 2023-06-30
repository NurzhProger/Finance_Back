from django.http import HttpResponse
from rest_framework import pagination, response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json
from datetime import datetime, timedelta
import calendar
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

    queryset_tbl1 = izm_inc_tbl1.objects.filter(_izm_inc_id=queryset_doc.id)
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

  
    # Получаем остатки по классиф-ям поступлении организации
    # remains = getincplanbyclassif(doc_req['_organization'], date = datetime.strptime(doc_req['_date'], '%d.%m.%Y'))

    # Фрагмент проверки сумм изменении и остатков
    masserror = []
    # for itm in tbl1_req:
    #     if not itm['tip'] == 'sm':
    #         continue
    #     ost = [person for person in remains if person['_classification_id'] == itm['_classification']]
    #     if len(ost)==0:
    #         return HttpResponse('{"status": "Нет остатков сумм по классификации ' + itm['classification_name'] + '"}', content_type="application/json", status = 400)
    #     for count in range(1, 13):
    #         if (itm['sm'+str(count)] + ost[0]['sm'+str(count)]) < 0:
    #             masserror.append({"_classification": itm['_classification'],  "month":count})

    # Если массив не пустой, то возвращаем ошибку с описанием
    if len(masserror)>0:
        return HttpResponse('{"status": "Нет остатков сумм по выбранным спецификам"}', content_type="application/json", status = 400)
                    
    # Запис шапки документа изменения по поступлениям
    try:
        date_object = datetime.strptime(doc_req['_date'], '%d.%m.%Y')
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
        date = datetime.strptime(strdate,"%d.%m.%Y").date()
    
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
# ***Сервисы утвержденного плана финансирования по поступлениям***
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
    obligs = data['obligs']

    try:
        if doc_req['id'] == None:
            date_object = datetime.strptime(doc_req['_date'], '%Y-%m-%d')
            year = date_object.year
            org = organization.objects.get(id=doc_req['_organization'])
            doc_cnt = utv_exp.objects.filter(date__year = year).count()
            itemdoc = utv_exp()
            itemdoc._organization_id = doc_req['_organization']
            itemdoc._budjet_id = org._budjet.id
            itemdoc._date = doc_req['_date']
            itemdoc.nom = str(doc_cnt + 1) + '-' + org.bin
            itemdoc.save()
        else:
            org = organization.objects.get(id=doc_req['_organization'])
            itemdoc = utv_exp.objects.get(id = doc_req['id'])
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
            for itemtbl1 in payments:
                newitemtbl1 = utv_exp_paym()
                newitemtbl1._utv_exp_id = itemdoc.id
                newitemtbl1._fkr_id = itemtbl1['_classification']
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
            for itemtbl1 in obligs:
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
# *****Сервисы импорт по поступлениям 2-19*****
# ****************************************************************
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def import219(request):
    pdftotext()
    return HttpResponse('{"status": "Ошибка получения данных"}', content_type="application/json", status = 200)






