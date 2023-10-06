from djoser.serializers import TokenCreateSerializer

class CustomTokenCreateSerializer(TokenCreateSerializer):
    def create(self, validated_data):
        # Получите идентификатор пользователя
        user = self.user

        # Аннулируйте предыдущий токен доступа
        user.auth_token.delete()

        # Создайте новый токен доступа
        token = super().create(validated_data)

        return token
