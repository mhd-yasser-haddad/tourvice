from rest_framework import serializers
from post.models import Post, Image, Like, Comment, CommentLike


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'image', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data['value'] != 0 and data['value'] != 1 and data['value'] != 2:
            raise serializers.ValidationError("The value only can be 0 or 1 or 2")
        return data

    class Meta:
        model = Like
        fields = ['value']


class CommentLikeSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data['value'] != 0 and data['value'] != 1 and data['value'] != 2:
            raise serializers.ValidationError("The value only can be 0 or 1 or 2")
        return data

    class Meta:
        model = CommentLike
        fields = ['value']


class CommentSerializer(serializers.ModelSerializer):
    def validate(self, data):
        string = data['comment'].replace(" ", "")
        if string == "" or string is None:
            raise serializers.ValidationError("Comment can not be empty")
        return data

    class Meta:
        model = Comment
        fields = ['comment', 'likes']


class PostSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data['post_type'] != 0 and data['post_type'] != 1:
            raise serializers.ValidationError("Post type should 0 or 1")
        return data

    class Meta:
        model = Post
        fields = ['id', 'description', 'post_type']
