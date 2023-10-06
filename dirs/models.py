from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# ****************************************************************
# ****************Модели справочников системные********************
# ****************************************************************
class budjet(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    adress = models.TextField(null=True)
    _parent = models.ForeignKey('self', blank=True, null = True, on_delete=models.CASCADE, verbose_name='Бюджет региона')
    def __str__(self):
        return self.name_rus

    def get_hierarchy_ids(self, include_self=True):
        ids = [self.id] if include_self else []
        children = budjet.objects.filter(_parent=self)
        for child in children:
            ids.extend(child.get_hierarchy_ids())
        return ids


class abp(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    

class organization(models.Model):
    bin = models.TextField(null=True)
    codeorg = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    adress = models.TextField(null=True)
    _budjet = models.ForeignKey(budjet, blank=True, on_delete=models.CASCADE, verbose_name='Бюджет региона')
    _abp = models.ForeignKey(abp, blank=True, null=True, on_delete=models.CASCADE, verbose_name='АБП')
    deleted = models.BooleanField(default=False, null=True)


class parent_organizations(models.Model):
    _date = models.DateTimeField(null=True, default=datetime(datetime.now().year, 1, 1, 0, 0, 0))
    _organization = models.ForeignKey(organization, blank=True, null=True, on_delete=models.CASCADE, related_name='child_organization')
    _parent = models.ForeignKey(organization, blank=True, null=True, on_delete=models.CASCADE, related_name='parent_organization')
    # _organization_parent = models.BigIntegerField(blank=True, null=True, verbose_name='Родительская организация')
    


class profile(models.Model):
    _user = models.OneToOneField(User, on_delete=models.CASCADE)
    _organization = models.ForeignKey(organization, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Текущая организация')


class type_izm_doc(models.Model):
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)


class loginhistory(models.Model):
    _date = models.DateTimeField(null=True, blank=True)
    username = models.TextField(null=True, blank=True)
    status = models.TextField(null=True, blank=True)
    client_ip = models.TextField(null=True, blank=True)







# ****************************************************************
# ****************Модели справочников доходов********************
# ****************************************************************
class category_income(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)


class class_income(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    _category = models.ForeignKey(category_income, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Категория')



class podclass_income(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    _classs = models.ForeignKey(class_income, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Класс')


class spec_income(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    _podclass = models.ForeignKey(podclass_income, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Подкласс')


class classification_income(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    _category = models.ForeignKey(category_income, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Категория')
    _classs = models.ForeignKey(class_income, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Класс')
    _podclass = models.ForeignKey(podclass_income, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Подкласс')
    _spec = models.ForeignKey(spec_income, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Специфика')








# ****************************************************************
# ****************Модели справочников расхода********************
# ****************************************************************
class funcgroup(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)


class funcpodgroup(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    _funcgroup = models.ForeignKey(funcgroup, blank=True, on_delete=models.CASCADE, verbose_name='Фнкциональная группа')



class program(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    _funcgroup = models.BigIntegerField(blank=True, null=True)
    _funcpodgroup = models.ForeignKey(funcpodgroup, blank=True, on_delete=models.CASCADE, verbose_name='АБП')
    _abp = models.ForeignKey(abp, blank=True, on_delete=models.CASCADE, verbose_name='АБП')
    


class podprogram(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    _funcgroup = models.BigIntegerField(blank=True, null=True)
    _funcpodgroup = models.BigIntegerField(blank=True, null=True)
    _abp = models.BigIntegerField(blank=True, null=True)
    _program = models.ForeignKey(program, blank=True, on_delete=models.CASCADE, verbose_name='АБП')



class fkr(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    _funcgroup = models.BigIntegerField(blank=True, null=True)
    _funcpodgroup = models.BigIntegerField(blank=True, null=True)
    _abp = models.BigIntegerField(blank=True, null=True)
    _program = models.ForeignKey(program, blank=True, on_delete=models.CASCADE, verbose_name='Программа расхода')
    _podprogram = models.ForeignKey(podprogram, blank=True, null=True, on_delete=models.CASCADE, verbose_name='Подпрограмма расхода')


class spec_exp(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)










