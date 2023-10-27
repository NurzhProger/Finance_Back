from rest_framework import serializers
from .models import *



class shareSerializer(serializers.ModelSerializer):
    class Meta:
        model = category_income
        fields = '__all__'

class abpSerializer(serializers.ModelSerializer):
    class Meta:
        model = abp
        fields = '__all__'


class fkrMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = fkr
        fields = ['id', 'code', 'name_rus']

class specexpSerializer(serializers.ModelSerializer):
    class Meta:
        model = spec_exp
        fields = '__all__'

class typedocSerializer(serializers.ModelSerializer):
    # _type_izm_doc = serializers.IntegerField(source = 'id')
    # type_izm_name = serializers.CharField(source = 'name_rus')
    class Meta:
        model = type_izm_doc
        fields = '__all__'

        
class budjetSerializer(serializers.ModelSerializer):
    class Meta:
        model = budjet
        fields = '__all__'


class budjetMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = budjet
        fields = ['id', 'name_rus']


class organizationMinSerializer(serializers.ModelSerializer):
    class Meta:
        model = organization
        fields = ['id', 'name_rus']


class parent_organizationsSerializer(serializers.ModelSerializer):
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    _parent = organizationMinSerializer()
    class Meta:
        model = parent_organizations
        fields = '__all__'


class organizationSerializer(serializers.ModelSerializer):
    _budjet = budjetSerializer()
    class Meta:
        model = organization
        fields = '__all__'


class userlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'is_active']


class useritemSerializer(serializers.ModelSerializer):
    last_login = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    date_joined = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = User
        # fields = '__all__'
        exclude = ['password', 'is_superuser', 'is_staff', 'groups', 'user_permissions']



class profileSerializer(serializers.ModelSerializer):
    _organization = organizationSerializer()
    class Meta:
        model = profile
        fields = '__all__'



class loginhistorySerializer(serializers.ModelSerializer):
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = loginhistory
        fields = '__all__'


class organizationMinSerializer(serializers.ModelSerializer):
    _budjet = budjetMinSerializer()
    class Meta:
        model = organization
        fields = ['id', 'name_rus', '_budjet']



class classificatinIncSerializer(serializers.ModelSerializer):
    class Meta:
        model = classification_income
        fields = ('id', 'name_kaz', 'name_rus', 'code')
    

class categoryIncSerializer(serializers.ModelSerializer):
    class Meta:
        model = category_income
        fields = '__all__'

class classIncSerializer(serializers.ModelSerializer):
    class Meta:
        model = class_income
        fields = '__all__'

class podclassIncSerializer(serializers.ModelSerializer):
    class Meta:
        model = podclass_income
        fields = '__all__'

class specIncSerializer(serializers.ModelSerializer):
    class Meta:
        model = spec_income
        fields = '__all__'

class classificatinIncDetailSerializer(serializers.ModelSerializer):
    _category = categoryIncSerializer()
    _classs = classIncSerializer()
    _podclass = podclassIncSerializer()
    _spec = specIncSerializer()
    
    class Meta:
        model = classification_income
        fields = '__all__'