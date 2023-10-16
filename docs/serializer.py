from rest_framework import serializers
from .models import *
from dirs.serializer import *


class utv_inc_Serializer(serializers.ModelSerializer):
    # org_name = serializers.CharField(source = '_organization.name_rus')
    # budjet_name = serializers.CharField(source = '_budjet.name_kaz')
    _organization = organizationSerializer()
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_inc
        fields = '__all__'
   

class utv_inc_tbl1_Serializer(serializers.ModelSerializer):
    _classification = classificatinIncSerializer()
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_inc_tbl1
        fields = '__all__'
    
 
class izm_inc_Serializer(serializers.ModelSerializer):
    _organization = organizationSerializer()
    _type_izm_doc = typedocSerializer()
    # org_name = serializers.CharField(source = '_organization.name_rus')
    # type_izm_name = serializers.CharField(source = '_type_izm_doc.name_rus')
    # budjet_name = serializers.CharField(source = '_budjet.name_kaz')
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_inc
        fields = '__all__'
        

class izm_inc_tbl1_Serializer(serializers.ModelSerializer):
    _classification = classificatinIncSerializer(read_only = True)
    # classification_name = serializers.CharField(source = '_classification.name_rus')
    # classification_code = serializers.CharField(source = '_classification.code')
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_inc_tbl1
        fields = '__all__'



class utv_exp_Serializer(serializers.ModelSerializer):
    _organization = organizationSerializer()
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_exp
        # fields = '__all__'
        exclude = ['_budjet']


class utv_exp_paymentserial(serializers.ModelSerializer):
    _fkr = fkrMinSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_exp_pay
        # fields = '__all__'
        exclude = ['_utv_exp','_organization']


class utv_exp_obligatserial(serializers.ModelSerializer):
    _fkr = fkrMinSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_exp_obl
        # fields = '__all__'
        exclude = ['_utv_exp','_organization']


class izm_exp_pay_serial(serializers.ModelSerializer):
    _fkr = fkrMinSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    # _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_exp_pay
        exclude = ['_date', '_organization', '_budjet', 'deleted', 'utvgod', 'god', 'itoggod', '_izm_exp']



class izm_exp_obl_serial(serializers.ModelSerializer):
    _fkr = fkrMinSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    # _date = serializers.DateField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_exp_obl
        exclude = ['_date', '_organization', '_budjet', 'deleted', 'utvgod', 'god', 'itoggod', '_izm_exp']



class izm_exp_serial(serializers.ModelSerializer):
    _organization = organizationMinSerializer()
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    _type_izm_doc = typedocSerializer()
    # izm_exp_pay_set = izm_exp_pay_serial(many = True)
    # izm_exp_obl_set = izm_exp_obl_serial(many = True)
    class Meta:
        model = izm_exp
        exclude = ['_budjet']



class import_serial(serializers.ModelSerializer):
    _organization = organizationMinSerializer()
    _budjet = budjetSerializer()
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = import219
        fields = "__all__"













