from rest_framework import serializers
from docs.models import *
# from dirs.serializer import *

class organizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = organization
        fields = '__all__'


class funcgroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = funcgroup
        fields = '__all__'

class funcpodgroupSerializer(serializers.ModelSerializer):
    _funcgroup = funcgroupSerializer()
    class Meta:
        model = funcpodgroup
        fields = '__all__'

class abpSerializer(serializers.ModelSerializer):
    class Meta:
        model = abp
        fields = '__all__'


class progSerializer(serializers.ModelSerializer):
    _funcpodgroup = funcpodgroupSerializer()
    _abp  = abpSerializer()
    class Meta:
        model = program
        fields = '__all__'


class podprogSerializer(serializers.ModelSerializer):
    _program = progSerializer()
    class Meta:
        model = podprogram
        fields = '__all__'

class specexpSerializer(serializers.ModelSerializer):
    class Meta:
        model = spec_exp
        fields = '__all__'

class fkrSerializer(serializers.ModelSerializer):
    _podprogram = podprogSerializer()
    # _abp = abpSerializer(read_only = True)
    class Meta:
        model = fkr
        fields = '__all__'


class exp_paymentserial(serializers.ModelSerializer):
    _organization = organizationSerializer()
    _fkr = fkrSerializer()
    _spec = specexpSerializer(read_only = True)
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_exp_pay
        # fields = '__all__'
        exclude = ['_utv_exp']





class utv_exp_obligatserial(serializers.ModelSerializer):
    _fkr = fkrSerializer(read_only = True)
    _spec = specexpSerializer(read_only = True)
    _date = serializers.DateTimeField(format='%d.%m.%Y %H:%M:%S')
    class Meta:
        model = utv_exp_obl
        # fields = '__all__'
        exclude = ['_utv_exp','_organization']





