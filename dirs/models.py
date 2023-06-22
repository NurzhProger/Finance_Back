from django.db import models


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


class budjet(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    adress = models.TextField(null=True)


class type_izm_doc(models.Model):
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)


class organization(models.Model):
    bin = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)
    adress = models.TextField(null=True)
    _budjet = models.ForeignKey(budjet, blank=True, on_delete=models.CASCADE, verbose_name='Бюджет региона')
    deleted = models.BooleanField(default=False, null=True)
    # _region = models.ForeignKey(budjet, blank=True, on_delete=models.CASCADE, verbose_name='Расположение организации')




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


class abp(models.Model):
    code = models.TextField(null=True)
    name_kaz = models.TextField(null=True)
    name_rus = models.TextField(null=True)


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










