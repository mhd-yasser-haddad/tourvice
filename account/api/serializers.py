from rest_framework import serializers

from account.models import Account


class RegistrationSerializer(serializers.ModelSerializer):

    confirm_password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = Account
        fields = ['email', 'username', 'name', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def save(self, verificationCode):
        account = Account(
            email=self.validated_data['email'],
            verification_code=verificationCode,
            username=self.validated_data['username'],
            name=self.validated_data['name']
        )
        password = self.validated_data['password']
        confirm_password = self.validated_data['confirm_password']

        if password != confirm_password:
            raise serializers.ValidationError({'message': 'Password and confirm password must match'})

        account.set_password(password)
        account.save()
        return account


class UserImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)

    class Meta:
        model = Account
        fields = ['image']


class UserFileSerializer(serializers.ModelSerializer):
    document = serializers.FileField(required=True)

    class Meta:
        model = Account
        fields = ['document']
