from rest_framework import serializers
from place.models import Place, Image, Rate, Comment, CommentLike


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['image']


# class UnreviewedPlaceSerializer(serializers.ModelSerializer):
#     images = ImageSerializer(many=True)
#
#     class Meta:
#         model = Place
#         fields = ['id', 'name', 'description', 'longtiude', 'latitude', 'images']


class RateSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data['rate'] < 1 or data['rate'] > 5:
            raise serializers.ValidationError("Rate have to be between 1 and 5 only")
        return data

    class Meta:
        model = Rate
        fields = ['rate']


class CommentLikeSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data['value'] != 0 and data['value'] != 1 and data['value'] != 2:
            raise serializers.ValidationError("The value only can be 0 or 1 or 2")
        return data

    class Meta:
        model = CommentLike
        fields = ['value']


class CommentSerializer(serializers.ModelSerializer):
    # likes = CommentLikeSerializer(many=True)

    def validate(self, data):
        string = data['comment'].replace(" ", "")
        if string == "" or string is None:
            raise serializers.ValidationError("Comment can not be empty")
        return data

    class Meta:
        model = Comment
        fields = ['comment', 'likes']


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'name', 'description', 'longtiude', 'latitude']
