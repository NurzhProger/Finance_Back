from rest_framework import serializers
from .models import *


class utv_inc_Serializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source = '_organization.name_rus')
    budjet_name = serializers.CharField(source = '_budjet.name_kaz')
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = utv_inc
        fields = '__all__'
   

class utv_inc_tbl1_Serializer(serializers.ModelSerializer):
    classification_name = serializers.CharField(source = '_classification.name_rus')
    classification_code = serializers.CharField(source = '_classification.code')
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = utv_inc_tbl1
        fields = '__all__'
    
 
class izm_inc_Serializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source = '_organization.name_rus')
    type_izm_name = serializers.CharField(source = '_type_izm_doc.name_rus')
    budjet_name = serializers.CharField(source = '_budjet.name_kaz')
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = izm_inc
        fields = '__all__'
        

class izm_inc_tbl1_Serializer(serializers.ModelSerializer):
    classification_name = serializers.CharField(source = '_classification.name_rus')
    classification_code = serializers.CharField(source = '_classification.code')
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = izm_inc_tbl1
        fields = '__all__'



class utv_exp_Serializer(serializers.ModelSerializer):
    org_name = serializers.CharField(source = '_organization.name_rus')
    budjet_name = serializers.CharField(source = '_budjet.name_kaz')
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = utv_exp
        fields = '__all__'


class utv_exp_paymentserial(serializers.ModelSerializer):
    fkr_name = serializers.CharField(source = '_fkr.name_rus')
    fkr_code = serializers.CharField(source = '_fkr.code')
    spec_name = serializers.CharField(source = '_spec.name_rus')
    spec_code = serializers.CharField(source = '_spec.code')
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = utv_exp_paym
        fields = '__all__'


class utv_exp_obligatserial(serializers.ModelSerializer):
    fkr_name = serializers.CharField(source = '_fkr.name_rus')
    fkr_code = serializers.CharField(source = '_fkr.code')
    spec_name = serializers.CharField(source = '_spec.name_rus')
    spec_code = serializers.CharField(source = '_spec.code')
    _date = serializers.DateField(format='%d.%m.%Y')
    class Meta:
        model = utv_exp_oblig
        fields = '__all__'












