from django.db import models
from dirs.models import *

# Утвержденный план по поступлениям
class utv_inc(models.Model):
    nom = models.TextField(null=True)
    _date = models.DateField(null=True)
    _organization = models.ForeignKey(organization, blank=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    _budjet = models.ForeignKey(budjet, blank=True, on_delete=models.CASCADE, verbose_name='Бюджет документа')
    deleted = models.BooleanField(default=False, null=True)
   

# ТЧ утвержденного плана по поступлениям
class utv_inc_tbl1(models.Model):
    _utv_inc = models.ForeignKey(utv_inc, blank=True, on_delete=models.CASCADE, verbose_name='ИД документа')
    _classification = models.ForeignKey(classification_income, blank=True, on_delete=models.CASCADE, verbose_name='Классификация документа')
    _organization = models.ForeignKey(organization, null=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    deleted = models.BooleanField(default=False, null=True)
    god = models.FloatField(null=True)
    sm1 = models.FloatField(null=True)
    sm2 = models.FloatField(null=True)
    sm3 = models.FloatField(null=True)
    sm4 = models.FloatField(null=True)
    sm5 = models.FloatField(null=True)
    sm6 = models.FloatField(null=True)
    sm7 = models.FloatField(null=True)
    sm8 = models.FloatField(null=True)
    sm9 = models.FloatField(null=True)
    sm10 = models.FloatField(null=True)
    sm11 = models.FloatField(null=True)
    sm12 = models.FloatField(null=True)
    _date = models.DateField(null=True)


# Изменение плана по поступлениям
class izm_inc(models.Model):
    nom = models.TextField(null=True)
    _date = models.DateField(null=True)
    _organization = models.ForeignKey(organization, blank=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    _budjet = models.ForeignKey(budjet, blank=True, on_delete=models.CASCADE, verbose_name='Бюджет документа')
    _type_izm_doc = models.ForeignKey(type_izm_doc, null=True, on_delete=models.CASCADE, verbose_name='Тип справки')
    deleted = models.BooleanField(default=False, null=True)

# ТЧ изменения плана по поступлениям
class izm_inc_tbl1(models.Model):
    _izm_inc = models.ForeignKey(izm_inc, blank=True, on_delete=models.CASCADE, verbose_name='ИД документа')
    _classification = models.ForeignKey(classification_income, blank=True, on_delete=models.CASCADE, verbose_name='Классификация документа')
    _organization = models.ForeignKey(organization, null=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    _budjet = models.ForeignKey(budjet, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Бюджет документа')
    deleted = models.BooleanField(default=False, null=True)
    _date = models.DateField(null=True)

    # Утвержденные суммы
    utvgod = models.FloatField(null=True)
    utv1 = models.FloatField(null=True)
    utv2 = models.FloatField(null=True)
    utv3 = models.FloatField(null=True)
    utv4 = models.FloatField(null=True)
    utv5 = models.FloatField(null=True)
    utv6 = models.FloatField(null=True)
    utv7 = models.FloatField(null=True)
    utv8 = models.FloatField(null=True)
    utv9 = models.FloatField(null=True)
    utv10 = models.FloatField(null=True)
    utv11 = models.FloatField(null=True)
    utv12 = models.FloatField(null=True)

    # Суммы изменении
    god = models.FloatField(null=True)
    sm1 = models.FloatField(null=True)
    sm2 = models.FloatField(null=True)
    sm3 = models.FloatField(null=True)
    sm4 = models.FloatField(null=True)
    sm5 = models.FloatField(null=True)
    sm6 = models.FloatField(null=True)
    sm7 = models.FloatField(null=True)
    sm8 = models.FloatField(null=True)
    sm9 = models.FloatField(null=True)
    sm10 = models.FloatField(null=True)
    sm11 = models.FloatField(null=True)
    sm12 = models.FloatField(null=True)

    # Суммы итогов
    itoggod = models.FloatField(null=True)
    itog1 = models.FloatField(null=True)
    itog2 = models.FloatField(null=True)
    itog3 = models.FloatField(null=True)
    itog4 = models.FloatField(null=True)
    itog5 = models.FloatField(null=True)
    itog6 = models.FloatField(null=True)
    itog7 = models.FloatField(null=True)
    itog8 = models.FloatField(null=True)
    itog9 = models.FloatField(null=True)
    itog10 = models.FloatField(null=True)
    itog11 = models.FloatField(null=True)
    itog12 = models.FloatField(null=True)




# Утвержденный план по расходам
class utv_exp(models.Model):
    nom = models.TextField(null=True)
    _date = models.DateField(null=True)
    _organization = models.ForeignKey(organization, blank=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    _budjet = models.ForeignKey(budjet, blank=True, on_delete=models.CASCADE, verbose_name='Бюджет документа')
    deleted = models.BooleanField(default=False, null=True)
   

# ТЧ платежи утвержденного плана по расходам
class utv_exp_paym(models.Model):
    _utv_exp = models.ForeignKey(utv_exp, blank=True, on_delete=models.CASCADE, verbose_name='ИД документа')
    _fkr = models.ForeignKey(fkr, blank=True, on_delete=models.CASCADE, verbose_name='ФКР')
    _spec = models.ForeignKey(spec_exp, blank=True, on_delete=models.CASCADE, verbose_name='Специфика')
    _organization = models.ForeignKey(organization, null=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    _date = models.DateField(null=True)
    deleted = models.BooleanField(default=False, null=True)
    god = models.FloatField(null=True)
    sm1 = models.FloatField(null=True)
    sm2 = models.FloatField(null=True)
    sm3 = models.FloatField(null=True)
    sm4 = models.FloatField(null=True)
    sm5 = models.FloatField(null=True)
    sm6 = models.FloatField(null=True)
    sm7 = models.FloatField(null=True)
    sm8 = models.FloatField(null=True)
    sm9 = models.FloatField(null=True)
    sm10 = models.FloatField(null=True)
    sm11 = models.FloatField(null=True)
    sm12 = models.FloatField(null=True)
    


# ТЧ обязательства утвержденного плана по расходам
class utv_exp_oblig(models.Model):
    _utv_exp = models.ForeignKey(utv_exp, blank=True, on_delete=models.CASCADE, verbose_name='ИД документа')
    _fkr = models.ForeignKey(fkr, blank=True, on_delete=models.CASCADE, verbose_name='ФКР')
    _spec = models.ForeignKey(spec_exp, blank=True, on_delete=models.CASCADE, verbose_name='Специфика')
    _organization = models.ForeignKey(organization, null=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    _date = models.DateField(null=True)
    deleted = models.BooleanField(default=False, null=True)
    god = models.FloatField(null=True)
    sm1 = models.FloatField(null=True)
    sm2 = models.FloatField(null=True)
    sm3 = models.FloatField(null=True)
    sm4 = models.FloatField(null=True)
    sm5 = models.FloatField(null=True)
    sm6 = models.FloatField(null=True)
    sm7 = models.FloatField(null=True)
    sm8 = models.FloatField(null=True)
    sm9 = models.FloatField(null=True)
    sm10 = models.FloatField(null=True)
    sm11 = models.FloatField(null=True)
    sm12 = models.FloatField(null=True)
    



































# Импорт форма 2-19 (поступления)
class import219(models.Model):
    nom = models.TextField(null=True)
    _date = models.DateField(null=True)
    _organization = models.ForeignKey(organization, blank=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    _budjet = models.ForeignKey(budjet, blank=True, on_delete=models.CASCADE, verbose_name='Бюджет документа')
    deleted = models.BooleanField(default=False, null=True)

# ТЧ импорт форма 2-19 (поступления)
class import219_tbl1(models.Model):
    _izm_inc = models.ForeignKey(izm_inc, blank=True, on_delete=models.CASCADE, verbose_name='ИД документа')
    _classification = models.ForeignKey(classification_income, blank=True, on_delete=models.CASCADE, verbose_name='Классификация документа')
    _organization = models.ForeignKey(organization, null=True, on_delete=models.CASCADE, verbose_name='Организация документа')
    _budjet = models.ForeignKey(budjet, blank=True, on_delete=models.CASCADE, verbose_name='Бюджет документа')
    _date = models.DateField(null=True)
    deleted = models.BooleanField(default=False, null=True)

    # Утвержденные суммы
    sm1 = models.FloatField(null=True) #Всего поступлений за день
    sm2 = models.FloatField(null=True) #Республиканский бюджет за день
    sm3 = models.FloatField(null=True) #Бюджет района (города обл-ого значения) за день
    sm4 = models.FloatField(null=True) #Обл. бюджет/ Астаны или г.Алматы за день
    sm5 = models.FloatField(null=True) #Бюджет МСУ за день
    sm6 = models.FloatField(null=True) #Всего поступлении с начала года
    sm7 = models.FloatField(null=True) #Республиканский бюджет с начала года
    sm8 = models.FloatField(null=True) #Бюджет района (города обл-ого значения) с начала года 
    sm9 = models.FloatField(null=True) #Обл. бюджет/ Астаны или г.Алматы с начала года
    sm10 = models.FloatField(null=True)#Бюджет МСУ с начала года




















    

    
