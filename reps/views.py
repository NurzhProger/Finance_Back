from django.http import HttpResponse
from rest_framework import pagination
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from dirs.models import *
from docs.models import *
from .serializer import *
from django.db import connection
from wsgiref.util import FileWrapper
import json, os, datetime

from openpyxl import load_workbook
from openpyxl.styles import Font, Border, Side, PatternFill
from openpyxl.worksheet.page import PageMargins, PrintPageSetup


import  jpype     
jpype.startJVM() 
from asposecells.api import Workbook

current_directory = os.path.dirname(__file__)



@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def report2728(request):
    
    datastr = request.body
    data = json.loads(datastr)
    id =  data['id']
    tip_rep = data['tip_rep']


    # Получаем текущий каталог скрипта
    relative_path = os.path.join(current_directory, "report_template", "report_2728.xlsx")
    wb = load_workbook(relative_path)
    ws = wb.active
    # ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    # Устанавливаем параметры печати и масштаб
    # page_setup = PrintPageSetup()
    # page_setup.fitToWidth = 0  # Оставьте 0 для автоматического масштабирования по ширине
    # page_setup.fitToHeight = 1  # Установите 1 для автоматического масштабирования по высоте
    # ws.page_setup = page_setup

    border = Border(left=Side(style='thin', color='000000'),
                right=Side(style='thin', color='000000'),
                top=Side(style='thin', color='000000'),
                bottom=Side(style='thin', color='000000'))

    light_gray_fill = PatternFill(start_color='FFDDDDDD',
                              end_color='FFDDDDDD',
                              fill_type='solid')

    query = f"""WITH zapros as (SELECT * FROM public.docs_izm_exp_{tip_rep}
                            WHERE _izm_exp_id={id}),
                    org as (SELECT * FROM public.dirs_organization
                            WHERE id in (select _organization_id from zapros)),
                    fkr as (SELECT * FROM public.dirs_fkr
                            WHERE id in (select _fkr_id from zapros)),
                    fg as (SELECT * FROM public.dirs_funcgroup
                            WHERE id in (select _funcgroup from fkr)),
                    fpg as (SELECT * FROM public.dirs_funcpodgroup
                            WHERE id in (select _funcpodgroup from fkr)),
                    abp as (SELECT * FROM public.dirs_abp
                            WHERE id in (select _abp from fkr)),
                    pr  as (SELECT * FROM public.dirs_program
                            WHERE id in (select _program_id from fkr)),
                    ppr as (SELECT * FROM public.dirs_podprogram
                            WHERE id in (select _podprogram_id from fkr)),
                    spec as (SELECT * FROM public.dirs_spec_exp
                            WHERE id in (select _spec_id from zapros)),
                    res as  (select 
                                    fg.code as fg_code, fg.name_rus as fg_name, 
                                    abp.code as abp_code, abp.name_rus as abp_name, 
                                    org.codeorg as org_code, org.name_rus as org_name,
                                    right(pr.code, 3) as pr_code, pr.name_rus as pr_name,
                                    right(ppr.code, 3) as ppr_code, ppr.name_rus as ppr_name,
                                    spec.code as spec_code, spec.name_rus as spec_name,
                                    sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8 + sm9 + sm10 + sm11 + sm12 as god,
                                    sm1,sm2,sm3,sm4,sm5,sm6,sm7,sm8,sm9,sm10,sm11,sm12
                                from zapros

                                left join fkr on
                                    zapros._fkr_id = fkr.id
                                left join fg on
                                    fkr._funcgroup = fg.id	
                                left join abp on
                                    fkr._abp = abp.id
                                left join org on
                                    zapros._organization_id = org.id
                                left join pr on
                                    fkr._program_id = pr.id
                                left join ppr on
                                    fkr._podprogram_id = ppr.id
                                left join spec on
                                    zapros._spec_id = spec.id)
                                    
                SELECT  fg_code, abp_code, org_code, pr_code, ppr_code, spec_code, 
                        '' as name,
                        sum(god), sum(sm1), sum(sm2), sum(sm3), sum(sm4), sum(sm5), sum(sm6), sum(sm7), sum(sm8), sum(sm9), sum(sm10), sum(sm11), sum(sm12),
                        max(fg_name), max(abp_name), max(org_name), max(pr_name), max(ppr_name), max(spec_name)
                FROM res 
                GROUP BY ROLLUP (fg_code, abp_code, org_code, pr_code, ppr_code, spec_code)
                order by fg_code NULLS FIRST, abp_code NULLS FIRST, org_code NULLS FIRST, pr_code NULLS FIRST, ppr_code NULLS FIRST, spec_code NULLS FIRST"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

  
    startrow = 17
    cnt = 0
    for row in result:
        color="FFFFFF"
        if (row[0] == None):
            continue

        ws.insert_rows(startrow + cnt)
        for i, value in enumerate(row, 1):
            if i > 20:
                continue
            if i==7: #если это наименование
                if (row[1]==None and row[2]==None and row[3]==None and row[4]==None and row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[20])
                elif (row[2]==None and row[3]==None and row[4]==None and row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[21])
                elif (row[3]==None and row[4]==None and row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[22])
                elif (row[4]==None and row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[23])
                elif (row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[24])
                else:
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[25])
            else:
                cell = ws.cell(row=startrow + cnt, column=i, value=value)
            cell.border  = border


            #Каждую строку меняем цвет фона чтобы было удобно пользователю
            if cnt % 2 == 0:
                cell.fill = light_gray_fill 
                color = "FFDDDDDD"   

            # Если это группировка, то в следующем, меняем цвет, чтобы не было видно  (типа иерархия)
            if (not value == None  and i>1 and i<7):
                ws.cell(row=startrow + cnt, column=i-1).font = Font(color=color)
        cnt += 1

    # ws.print_title_rows = "17:17"

    xlsx_temp = current_directory + "/temp_files/" + request.user.username + "_2728.xlsx"  
    pdf_temp = current_directory + "/temp_files/" + request.user.username + "_2728.pdf" 

    wb.save(xlsx_temp)
    workbook = Workbook(xlsx_temp)
    workbook.save(pdf_temp)

    pdf_file = open(pdf_temp, "rb")
    body = FileWrapper(pdf_file)

    resp =  HttpResponse(body, content_type="application/pdf")
    resp['Content-Disposition'] = 'attachment; filename="table.pdf"'
    pdf_file.close()
    return resp



@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def report2930(request):
    datastr = request.body
    data = json.loads(datastr)
    id =  data['id']
    tip_rep = data['tip_rep']

    # Получаем текущий каталог скрипта
    relative_path = os.path.join(current_directory, "report_template", "report_2930.xlsx")
    wb = load_workbook(relative_path)
    ws = wb.active


    border = Border(left=Side(style='thin', color='000000'),
                right=Side(style='thin', color='000000'),
                top=Side(style='thin', color='000000'),
                bottom=Side(style='thin', color='000000'))

    light_gray_fill = PatternFill(start_color='FFDDDDDD',
                              end_color='FFDDDDDD',
                              fill_type='solid')

    query = f"""WITH zapros as (SELECT * FROM public.docs_izm_exp_{tip_rep}
                            WHERE _izm_exp_id={id}),
                    org as (SELECT * FROM public.dirs_organization
                            WHERE id in (select _organization_id from zapros)),
                    fkr as (SELECT * FROM public.dirs_fkr
                            WHERE id in (select _fkr_id from zapros)),
                    fg as (SELECT * FROM public.dirs_funcgroup
                            WHERE id in (select _funcgroup from fkr)),
                    fpg as (SELECT * FROM public.dirs_funcpodgroup
                            WHERE id in (select _funcpodgroup from fkr)),
                    abp as (SELECT * FROM public.dirs_abp
                            WHERE id in (select _abp from fkr)),
                    pr  as (SELECT * FROM public.dirs_program
                            WHERE id in (select _program_id from fkr)),
                    ppr as (SELECT * FROM public.dirs_podprogram
                            WHERE id in (select _podprogram_id from fkr)),
                    spec as (SELECT * FROM public.dirs_spec_exp
                            WHERE id in (select _spec_id from zapros)),
                    res as  (select 
                                    fg.code as fg_code, fg.name_rus as fg_name, 
                                    abp.code as abp_code, abp.name_rus as abp_name, 
                                    right(pr.code, 3) as pr_code, pr.name_rus as pr_name,
                                    right(ppr.code, 3) as ppr_code, ppr.name_rus as ppr_name,
                                    spec.code as spec_code, spec.name_rus as spec_name,
                                    sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8 + sm9 + sm10 + sm11 + sm12 as god,
                                    sm1,sm2,sm3,sm4,sm5,sm6,sm7,sm8,sm9,sm10,sm11,sm12
                                from zapros

                                left join fkr on
                                    zapros._fkr_id = fkr.id
                                left join fg on
                                    fkr._funcgroup = fg.id	
                                left join abp on
                                    fkr._abp = abp.id
                                left join pr on
                                    fkr._program_id = pr.id
                                left join ppr on
                                    fkr._podprogram_id = ppr.id
                                left join spec on
                                    zapros._spec_id = spec.id)
                                    
                SELECT  fg_code, abp_code, pr_code, ppr_code, spec_code, 
                        '' as name,
                        sum(god), sum(sm1), sum(sm2), sum(sm3), sum(sm4), sum(sm5), sum(sm6), sum(sm7), sum(sm8), sum(sm9), sum(sm10), sum(sm11), sum(sm12),
                        max(fg_name), max(abp_name),max(pr_name), max(ppr_name), max(spec_name)
                FROM res 
                GROUP BY ROLLUP (fg_code, abp_code, pr_code, ppr_code, spec_code)
                order by fg_code NULLS FIRST, abp_code NULLS FIRST, pr_code NULLS FIRST, ppr_code NULLS FIRST, spec_code NULLS FIRST"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

  
    startrow = 14
    cnt = 0
    for row in result:
        color="FFFFFF"
        if (row[0] == None):
            continue

        ws.insert_rows(14 + cnt)
        for i, value in enumerate(row, 1):

            if i > 19:
                continue

            if i==6: #если это наименование
                if (row[1]==None and row[2]==None and row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[19])
                elif (row[2]==None and row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[20])
                elif (row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[21])
                elif (row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[22])
                else:
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[23])
            else:
                cell = ws.cell(row=startrow + cnt, column=i, value=value)
            cell.border  = border



            # cell = ws.cell(row=14 + cnt, column=i, value=value)
            # cell.border  = border

            if cnt % 2 == 0:
                cell.fill = light_gray_fill 
                color = "FFDDDDDD"         

            if (not value == None  and i>1 and i<6):
                ws.cell(row=14 + cnt, column=i-1).font = Font(color=color)
        cnt += 1

    ws.print_title_rows = "17:17"

    xlsx_temp = current_directory + "/temp_files/" + request.user.username + "_2930.xlsx"  
    pdf_temp = current_directory + "/temp_files/" + request.user.username + "_2930.pdf" 

    wb.save(xlsx_temp)
    workbook = Workbook(xlsx_temp)
    workbook.save(pdf_temp)

    pdf_file = open(pdf_temp, "rb")
    body = FileWrapper(pdf_file)

    resp =  HttpResponse(body, content_type="application/pdf")
    resp['Content-Disposition'] = 'attachment; filename="table.pdf"'
    pdf_file.close()
    return resp



@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def report3335(request):
    datastr = request.body
    data = json.loads(datastr)
    id =  data['id']
    tip_rep = data['tip_rep']

    # Получаем текущий каталог скрипта
    relative_path = os.path.join(current_directory, "report_template", "report_3335.xlsx")
    wb = load_workbook(relative_path)
    ws = wb.active


    border = Border(left=Side(style='thin', color='000000'),
                right=Side(style='thin', color='000000'),
                top=Side(style='thin', color='000000'),
                bottom=Side(style='thin', color='000000'))

    light_gray_fill = PatternFill(start_color='FFDDDDDD',
                              end_color='FFDDDDDD',
                              fill_type='solid')

    query = f"""WITH zapros as (SELECT * FROM public.docs_izm_exp_{tip_rep}
                            WHERE _izm_exp_id={id}),
                    org as (SELECT * FROM public.dirs_organization
                            WHERE id in (select _organization_id from zapros)),
                    fkr as (SELECT * FROM public.dirs_fkr
                            WHERE id in (select _fkr_id from zapros)),
                    fg as (SELECT * FROM public.dirs_funcgroup
                            WHERE id in (select _funcgroup from fkr)),
                    fpg as (SELECT * FROM public.dirs_funcpodgroup
                            WHERE id in (select _funcpodgroup from fkr)),
                    abp as (SELECT * FROM public.dirs_abp
                            WHERE id in (select _abp from fkr)),
                    pr  as (SELECT * FROM public.dirs_program
                            WHERE id in (select _program_id from fkr)),
                    ppr as (SELECT * FROM public.dirs_podprogram
                            WHERE id in (select _podprogram_id from fkr)),
                    spec as (SELECT * FROM public.dirs_spec_exp
                            WHERE id in (select _spec_id from zapros)),
                    res as  (select 
                                    fg.code as fg_code, fg.name_rus as fg_name, 
                                    abp.code as abp_code, abp.name_rus as abp_name,
                                    org.codeorg as org_code,  org.name_rus as org_name,
                                    right(pr.code, 3) as pr_code, pr.name_rus as pr_name,
                                    right(ppr.code, 3) as ppr_code, ppr.name_rus as ppr_name,
                                    spec.code as spec_code, spec.name_rus as spec_name,
                                    sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8 + sm9 + sm10 + sm11 + sm12 as god,
                                    sm1,sm2,sm3,sm4,sm5,sm6,sm7,sm8,sm9,sm10,sm11,sm12
                                from zapros
                                left join org on
                                    zapros._organization_id = org.id
                                left join fkr on
                                    zapros._fkr_id = fkr.id
                                left join fg on
                                    fkr._funcgroup = fg.id	
                                left join abp on
                                    fkr._abp = abp.id
                                left join pr on
                                    fkr._program_id = pr.id
                                left join ppr on
                                    fkr._podprogram_id = ppr.id
                                left join spec on
                                    zapros._spec_id = spec.id)
                                    
                SELECT  '' as name, abp_code, org_code, pr_code, ppr_code, spec_code, 
                        sum(god), sum(sm1), sum(sm2), sum(sm3), sum(sm4), sum(sm5), sum(sm6), sum(sm7), sum(sm8), sum(sm9), sum(sm10), sum(sm11), sum(sm12),
                        max(abp_name), max(org_name), max(pr_name), max(ppr_name), max(spec_name)
                FROM res 
                GROUP BY ROLLUP (abp_code, org_code, pr_code, ppr_code, spec_code)
                order by abp_code NULLS FIRST, org_code NULLS FIRST, pr_code NULLS FIRST, ppr_code NULLS FIRST, spec_code NULLS FIRST"""

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

  
    startrow = 21
    cnt = 0
    for row in result:
        color="FFFFFF"
        if (row[1] == None):
            continue

        ws.insert_rows(startrow + cnt)
        for i, value in enumerate(row, 1):

            if i > 19:
                continue

            if i==1: #если это наименование
                if (row[2]==None and row[3]==None and row[4]==None and row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[19])
                elif (row[3]==None and row[4]==None and row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[20])
                elif (row[4]==None and row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[21])
                elif (row[5]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[22])
                else:
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[23])
                # cell.alignment = cell.alignment.copy(wrap_text=True)
            else:
                cell = ws.cell(row=startrow + cnt, column=i, value=value)
            cell.border  = border


            if cnt % 2 == 0:
                cell.fill = light_gray_fill 
                color = "FFDDDDDD"         

            if (not value == None  and i>2 and i<6):
                ws.cell(row=startrow + cnt, column=i-1).font = Font(color=color)
        cnt += 1

    # ws.print_title_rows = "17:17"

    xlsx_temp = current_directory + "/temp_files/" + request.user.username + "_3335.xlsx"  
    pdf_temp = current_directory + "/temp_files/" + request.user.username + "_3335.pdf" 

    wb.save(xlsx_temp)
    workbook = Workbook(xlsx_temp)
    workbook.save(pdf_temp)

    pdf_file = open(pdf_temp, "rb")
    body = FileWrapper(pdf_file)

    resp =  HttpResponse(body, content_type="application/pdf")
    resp['Content-Disposition'] = 'attachment; filename="table.pdf"'
    pdf_file.close()
    return resp



@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def report2_5(request):
    datastr = request.body
    data = json.loads(datastr)
    org_id =  data['_organization_id']
    tip_rep = data['tip_rep']
    if not (tip_rep == "pay" or tip_rep == "obl"):
        return HttpResponse(json.dumps({"status": "Неверный тип отчета"}), content_type="application/json", status=400)
    
    if (org_id == 0):
        return HttpResponse(json.dumps({"status": "Выберите организацию"}), content_type="application/json", status=400)

    # Получаем текущий каталог скрипт
    relative_path = os.path.join(current_directory, "report_template", "report_2_5.xlsx")
    wb = load_workbook(relative_path)
    ws = wb.active


    border = Border(left=Side(style='thin', color='000000'),
                right=Side(style='thin', color='000000'),
                top=Side(style='thin', color='000000'),
                bottom=Side(style='thin', color='000000'))

    light_gray_fill = PatternFill(start_color='FFDDDDDD',
                              end_color='FFDDDDDD',
                              fill_type='solid')

    query = f"""with union_utv_izm as (SELECT _fkr_id, _spec_id, _organization_id, sum(sm1) as sm1, sum(sm2) as sm2, sum(sm3) as sm3, sum(sm4) as sm4, sum(sm5) as sm5, sum(sm6) as sm6, sum(sm7) as sm7, sum(sm8) as sm8, sum(sm9) as sm9, sum(sm10) as sm10, sum(sm11) as sm11, sum(sm12) as sm12 
                            FROM public.docs_reg_exp_{tip_rep}
                            WHERE _organization_id = {org_id}
                            GROUP BY _fkr_id, _spec_id,_organization_id),
                    org as (SELECT * FROM public.dirs_organization
                                            WHERE id in (select _organization_id from union_utv_izm)),
                    fkr as (SELECT * FROM public.dirs_fkr
                                            WHERE id in (select _fkr_id from union_utv_izm)),
                    fg as (SELECT * FROM public.dirs_funcgroup
                                            WHERE id in (select _funcgroup from fkr)),
                    fpg as (SELECT * FROM public.dirs_funcpodgroup
                                            WHERE id in (select _funcpodgroup from fkr)),
                    abp as (SELECT * FROM public.dirs_abp
                                            WHERE id in (select _abp from fkr)),
                    pr  as (SELECT * FROM public.dirs_program
                                            WHERE id in (select _program_id from fkr)),
                    ppr as (SELECT * FROM public.dirs_podprogram
                                            WHERE id in (select _podprogram_id from fkr)),
                    spec as (SELECT * FROM public.dirs_spec_exp
                                            WHERE id in (select _spec_id from union_utv_izm))

                    SELECT  
                        abp.code as abp_code, 
                        org.codeorg as org_code,  
                        right(pr.code, 3) as pr_code, 
                        right(ppr.code, 3) as ppr_code, 
                        spec.code as spec_code, 
                        '' as name,
                        sum(sm1 + sm2 + sm3 + sm4 + sm5 + sm6 + sm7 + sm8 + sm9 + sm10 + sm11 + sm12) as god,
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
                        COALESCE(sum(sm12),0) as sm12,
                        max(abp.name_rus) as abp_name,
                        max(org.name_rus) as org_name,
                        max(pr.name_rus) as pr_name,
                        max(ppr.name_rus) as ppr_name,
                        max(spec.name_rus) as spec_name
                    FROM union_utv_izm as fulldata
                    left join org on
                        fulldata._organization_id = org.id
                    left join fkr on
                        fulldata._fkr_id = fkr.id
                    left join abp on
                        fkr._abp = abp.id
                    left join pr on
                        fkr._program_id = pr.id
                    left join ppr on
                        fkr._podprogram_id = ppr.id
                    left join spec on
                        fulldata._spec_id = spec.id
                    GROUP BY ROLLUP (abp_code, org_code, pr_code, ppr_code, spec_code)
                    order by abp_code NULLS FIRST, org_code NULLS FIRST, pr_code NULLS FIRST, ppr_code NULLS FIRST, spec_code NULLS FIRST          
                """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

  
    startrow = 23
    cnt = 0
    for row in result:
        color="FFFFFF"
        if (row[0] == None):
            continue

        ws.insert_rows(startrow + cnt)
        for i, value in enumerate(row, 1):

            if i > 19:
                continue

            if i==6: #если это наименование
                if (row[1]==None and row[2]==None and row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[18])
                elif (row[2]==None and row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[19])
                elif (row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[20])
                elif (row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[21])
                else:
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[22])
            else:
                cell = ws.cell(row=startrow + cnt, column=i, value=value)
            cell.border  = border


            if cnt % 2 == 0:
                cell.fill = light_gray_fill 
                color = "FFDDDDDD"         

            if (not value == None  and i>1 and i<6):
                ws.cell(row=startrow + cnt, column=i-1).font = Font(color=color)
        cnt += 1

 
    xlsx_temp = current_directory + "/temp_files/" + request.user.username + "_2_5.xlsx"  
    pdf_temp = current_directory + "/temp_files/" + request.user.username + "_2_5.pdf" 

    wb.save(xlsx_temp)
    workbook = Workbook(xlsx_temp)
    workbook.save(pdf_temp)

    pdf_file = open(pdf_temp, "rb")
    body = FileWrapper(pdf_file)

    resp =  HttpResponse(body, content_type="application/pdf")
    resp['Content-Disposition'] = 'attachment; filename="table.pdf"'
    pdf_file.close()
    return resp


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def report_14(request):
    datastr = request.body
    data = json.loads(datastr)
    _budjet_id =  data['_budjet_id']
    tip_rep = data['_date']

 
    ids_bjt = budjet.objects.get(id = _budjet_id).get_hierarchy_ids()
    ids_bjt.append(0)#пустой ИД в конце, чтобы избавиться от лишнего ","
    kortej = tuple(ids_bjt)
 
 
  
    if (_budjet_id == 0):
        return HttpResponse(json.dumps({"status": "Выберите бюджет"}), content_type="application/json", status=400)

    # Получаем текущий каталог скрипт
    relative_path = os.path.join(current_directory, "report_template", "report_14.xlsx")
    wb = load_workbook(relative_path)
    ws = wb.active


    border = Border(left=Side(style='thin', color='000000'),
                right=Side(style='thin', color='000000'),
                top=Side(style='thin', color='000000'),
                bottom=Side(style='thin', color='000000'))

    light_gray_fill = PatternFill(start_color='FFDDDDDD',
                              end_color='FFDDDDDD',
                              fill_type='solid')

    query = f"""with reg as (SELECT * FROM docs_reg_inc where _budjet_id in {kortej}),
                        budjet as (select * from dirs_budjet
                                    where id in (select _budjet_id from reg)),
                        classif as (select * from dirs_classification_income
                                    where id in (select _classification_id from reg)),
                        cat as (select * from dirs_category_income
                                    where id in (select _category_id from classif)),
                        clas as (select * from dirs_class_income
                                    where id in (select _classs_id from classif)),
                        podcl as (select * from dirs_podclass_income
                                    where id in (select _podclass_id from classif)),
                        spec as (select * from dirs_spec_income
                                    where id in (select _spec_id from classif))


                    select  budjet.name_rus as budjet,
                            cat.code as cat, right(clas.code, 2) as classs, right(podcl.code, 1) as podclass, right(spec.code,2) as spec, 
                            '' as name,
                            sum(reg.god) as god, 
                            sum(reg.sm1) as sm1, 
                            sum(reg.sm2) as sm2, 
                            sum(reg.sm3) as sm3, 
                            sum(reg.sm4) as sm4, 
                            sum(reg.sm5) as sm5, 
                            sum(reg.sm6) as sm6, 
                            sum(reg.sm7) as sm7, 
                            sum(reg.sm8) as sm8, 
                            sum(reg.sm9) as sm9, 
                            sum(reg.sm10) as sm10, 
                            sum(reg.sm11) as sm11, 
                            sum(reg.sm12) as sm12,
                            '' as bjt_name, max(cat.name_rus) as cat_name, max(clas.name_rus) as classs_name, max(podcl.name_rus) as podclass_name, max(spec.name_rus) as spec_name
                    from reg
                    left join budjet on 
                        reg._budjet_id = budjet.id
                    left join classif on 
                        reg._classification_id = classif.id
                    left join cat on 
                        classif._category_id = cat.id
                    left join clas on 
                        classif._classs_id = clas.id
                    left join podcl on 
                        classif._podclass_id = podcl.id
                    left join spec on 
                        classif._spec_id = spec.id
                    group by rollup(budjet.name_rus, cat.code, clas.code, podcl.code, spec.code)
                    order by budjet.name_rus nulls first, cat.code nulls first, clas.code nulls first, podcl.code nulls first, spec.code nulls first
                """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

  
    startrow = 22
    cnt = 0
    for row in result:
        color="FFFFFF"
        # Пропуск общего итога
        if (row[0] == None):
            continue

        ws.insert_rows(startrow + cnt)
        for i, value in enumerate(row, 1):

            if i > 19:
                continue

            if i==6: #если это наименование
                if (row[1]==None and row[2]==None and row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[19])
                elif (row[2]==None and row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[20])
                elif (row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[21])
                elif (row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[22])
                else:
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[23])
            else:
                cell = ws.cell(row=startrow + cnt, column=i, value=value)
            cell.border  = border


            if cnt % 2 == 0:
                cell.fill = light_gray_fill 
                color = "FFDDDDDD"         

            if (not value == None  and i>1 and i<6):
                ws.cell(row=startrow + cnt, column=i-1).font = Font(color=color)
        cnt += 1

 
    xlsx_temp = current_directory + "/temp_files/" + request.user.username + "_14.xlsx"  
    pdf_temp = current_directory + "/temp_files/" + request.user.username + "_14.pdf" 

    wb.save(xlsx_temp)
    workbook = Workbook(xlsx_temp)
    workbook.save(pdf_temp)

    pdf_file = open(pdf_temp, "rb")
    body = FileWrapper(pdf_file)

    resp =  HttpResponse(body, content_type="application/pdf")
    resp['Content-Disposition'] = 'attachment; filename="table.pdf"'
    pdf_file.close()
    return resp




@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def report_25(request):
    datastr = request.body
    data = json.loads(datastr)
    _izm_inc_id =  data['_izm_inc_id']

 
  
    if (_izm_inc_id == 0):
        return HttpResponse(json.dumps({"status": "Выберите бюджет"}), content_type="application/json", status=400)

    # Получаем текущий каталог скрипт
    relative_path = os.path.join(current_directory, "report_template", "report_25.xlsx")
    wb = load_workbook(relative_path)
    ws = wb.active


    border = Border(left=Side(style='thin', color='000000'),
                right=Side(style='thin', color='000000'),
                top=Side(style='thin', color='000000'),
                bottom=Side(style='thin', color='000000'))

    light_gray_fill = PatternFill(start_color='FFDDDDDD',
                              end_color='FFDDDDDD',
                              fill_type='solid')

    query = f"""with reg as (SELECT * FROM docs_reg_inc where _izm_inc_id = {_izm_inc_id}),
                        budjet as (select * from dirs_budjet
                                    where id in (select _budjet_id from reg)),
                        classif as (select * from dirs_classification_income
                                    where id in (select _classification_id from reg)),
                        cat as (select * from dirs_category_income
                                    where id in (select _category_id from classif)),
                        clas as (select * from dirs_class_income
                                    where id in (select _classs_id from classif)),
                        podcl as (select * from dirs_podclass_income
                                    where id in (select _podclass_id from classif)),
                        spec as (select * from dirs_spec_income
                                    where id in (select _spec_id from classif))


                    select  '' as name,
                            cat.code as cat, right(clas.code, 2) as classs, right(podcl.code, 1) as podclass, right(spec.code,2) as spec,
                            sum(reg.god) as god, 
                            sum(reg.sm1) as sm1, 
                            sum(reg.sm2) as sm2, 
                            sum(reg.sm3) as sm3, 
                            sum(reg.sm4) as sm4, 
                            sum(reg.sm5) as sm5, 
                            sum(reg.sm6) as sm6, 
                            sum(reg.sm7) as sm7, 
                            sum(reg.sm8) as sm8, 
                            sum(reg.sm9) as sm9, 
                            sum(reg.sm10) as sm10, 
                            sum(reg.sm11) as sm11, 
                            sum(reg.sm12) as sm12,
                            max(cat.name_rus) as cat_name, max(clas.name_rus) as classs_name, max(podcl.name_rus) as podclass_name, max(spec.name_rus) as spec_name
                    from reg
                    left join budjet on 
                        reg._budjet_id = budjet.id
                    left join classif on 
                        reg._classification_id = classif.id
                    left join cat on 
                        classif._category_id = cat.id
                    left join clas on 
                        classif._classs_id = clas.id
                    left join podcl on 
                        classif._podclass_id = podcl.id
                    left join spec on 
                        classif._spec_id = spec.id
                    group by rollup(budjet.name_rus, cat.code, clas.code, podcl.code, spec.code)
                    order by budjet.name_rus nulls first, cat.code nulls first, clas.code nulls first, podcl.code nulls first, spec.code nulls first
                """

    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()

  
    startrow = 20
    cnt = 0
    for row in result:
        color="FFFFFF"
        # Пропуск общего итога
        if (row[1] == None):
            continue

        ws.insert_rows(startrow + cnt)
        for i, value in enumerate(row, 1):
            # i начинается от 1 по ширине колонок (количество)
            if i > 18:
                continue

            if i==1: #если это наименование
                if (row[2]==None and row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[18])
                elif (row[3]==None and row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[19])
                elif (row[4]==None):
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[20])
                else:
                    cell = ws.cell(row=startrow + cnt, column=i, value=row[21])
            else:
                cell = ws.cell(row=startrow + cnt, column=i, value=value)
            cell.border  = border


            if cnt % 2 == 0:
                cell.fill = light_gray_fill 
                color = "FFDDDDDD"         

            if (not value == None  and i>2 and i<6):
                ws.cell(row=startrow + cnt, column=i-1).font = Font(color=color)
        cnt += 1

 
    xlsx_temp = current_directory + "/temp_files/" + request.user.username + "_25.xlsx"  
    pdf_temp = current_directory + "/temp_files/" + request.user.username + "_25.pdf" 

    wb.save(xlsx_temp)
    workbook = Workbook(xlsx_temp)
    workbook.save(pdf_temp)

    pdf_file = open(pdf_temp, "rb")
    body = FileWrapper(pdf_file)

    resp =  HttpResponse(body, content_type="application/pdf")
    resp['Content-Disposition'] = 'attachment; filename="table.pdf"'
    pdf_file.close()
    return resp






