from rest_framework import serializers
from .models import *
from dirs.serializer import *


class utv_inc_Serializer(serializers.ModelSerializer):
    # org_name = serializers.CharField(source = '_organization.name_rus')
    # budjet_name = serializers.CharField(source = '_budjet.name_kaz')
    _organization = organizationMinSerializer()
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = utv_inc
        fields = '__all__'
   

class utv_inc_tbl1_Serializer(serializers.ModelSerializer):
    _classification = classificatinIncSerializer()
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = utv_inc_tbl1
        fields = '__all__'
    
 
class izm_inc_Serializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source = '_organization.name_rus')
    type_izm_name = serializers.CharField(source = '_type_izm_doc.name_rus')
    budjet_name = serializers.CharField(source = '_budjet.name_kaz')
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_inc
        fields = '__all__'
        

class izm_inc_tbl1_Serializer(serializers.ModelSerializer):
    classification_name = serializers.CharField(source = '_classification.name_rus')
    classification_code = serializers.CharField(source = '_classification.code')
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_inc_tbl1
        fields = '__all__'



class utv_exp_Serializer(serializers.ModelSerializer):
    _organization = organizationMinSerializer()
    _date = serializers.DateField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_exp
        # fields = '__all__'
        exclude = ['_budjet']


class utv_exp_paymentserial(serializers.ModelSerializer):
    _fkr = fkrMinSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    _date = serializers.DateField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_exp_paym
        # fields = '__all__'
        exclude = ['_utv_exp','_organization']


class utv_exp_obligatserial(serializers.ModelSerializer):
    _fkr = fkrMinSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    _date = serializers.DateField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_exp_oblig
        # fields = '__all__'
        exclude = ['_utv_exp','_organization']




class izm_exp_paym_Serializer(serializers.ModelSerializer):
    _organization = organizationMinSerializer()
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    _type_izm_doc = typedocSerializer()
    class Meta:
        model = izm_exp_paym
        exclude = ['_budjet']



class izm_exp_oblig_Serializer(serializers.ModelSerializer):
    _organization = organizationMinSerializer()
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_exp_oblig
        exclude = ['_budjet']


class izm_exp_paym_tbl_serial(serializers.ModelSerializer):
    _fkr = fkrMinSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    # _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_exp_paym_tbl
        exclude = ['_date', '_organization', '_budjet', 'deleted', 'utvgod', 'god', 'itoggod', '_izm_exp_paym']


class izm_exp_oblig_tbl_serial(serializers.ModelSerializer):
    _fkr = fkrMinSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    _date = serializers.DateField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = izm_exp_oblig_tbl
        exclude = ['_date', '_organization', '_budjet', 'deleted', 'utvgod', 'god', 'itoggod', '_izm_exp_oblig']











