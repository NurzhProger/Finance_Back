from rest_framework import serializers
from .models import *

class shareSerializer(serializers.ModelSerializer):
    class Meta:
        model = category_income
        fields = '__all__'

class typedocSerializer(serializers.ModelSerializer):
    _type_izm_doc = serializers.CharField(source = 'id')
    type_izm_name = serializers.CharField(source = 'name_rus')
    class Meta:
        model = type_izm_doc
        fields = ('_type_izm_doc', 'type_izm_name')

        
class organizationSerializer(serializers.ModelSerializer):
    budjet_name = serializers.CharField(source = '_budjet.name_rus')
    class Meta:
        model = organization
        fields = '__all__'


class classificatinIncSerializer(serializers.ModelSerializer):
    class Meta:
        model = classification_income
        fields = ('id', 'name_kaz', 'name_rus', 'code')
    

class classificatinIncDetailSerializer(serializers.ModelSerializer):
    category_code = serializers.CharField(source = '_category.code')
    category_name = serializers.CharField(source = '_category.name_rus')
    classs_code = serializers.CharField(source = '_classs.code')
    classs_name = serializers.CharField(source = '_classs.name_rus')
    podclass_code = serializers.CharField(source = '_podclass.code')
    podclass_name = serializers.CharField(source = '_podclass.name_rus')
    spec_code = serializers.CharField(source = '_spec.code')
    spec_name = serializers.CharField(source = '_spec.name_rus')
    class Meta:
        model = classification_income
        fields = ('id', 'name_kaz', 'name_rus', 'code', 
        '_category_id', 'category_code','category_name', 
        '_classs_id', 'classs_code','classs_name', 
        '_podclass_id', 'podclass_code','podclass_name',  
        '_spec_id', 'spec_code','spec_name')