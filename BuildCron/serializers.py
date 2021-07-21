from django.contrib.auth.models import User
from rest_framework import serializers
from BuildCron.models import *


class CustomUserSerializer(serializers.ModelSerializer):
    status = serializers.CharField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)  # as long as the fields are the same, we can just use this
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = '__all__'


class LicensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licenses
        fields = '__all__'

class LicensesApprovedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licenses
        fields = ('status', )


class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'


class ChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checklist
        fields = '__all__'


class QuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields = '__all__'

class QuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Queries
        fields = '__all__'



class FAQsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQs
        fields = '__all__'


class siteInstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = siteInstruction
        fields = '__all__'
