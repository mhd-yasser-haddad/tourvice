from django.db import models


def upload_location(instance, filename):
    file_path = 'posts/images/{username}/{created_at}-{filename}'.format(
        username=str(instance.user.name), created_at=str(instance.created_at), filename=filename
    )
    return file_path


class Post(models.Model):
    description         = models.TextField(unique=False, null=False)
    user                = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name="posting_user", null=False)
    place               = models.ForeignKey('place.Place', on_delete=models.CASCADE, related_name="place", null=True)
    post_type           = models.PositiveIntegerField(null=False)
    created_at	        = models.DateTimeField(verbose_name='created_at', auto_now_add=True)
    likes               = models.ManyToManyField('account.Account', through='Like', related_name='post_likes')
    comments            = models.ManyToManyField('account.Account', through='Comment', related_name='post_comments')

    def __str__(self):
        return self.description

class Image(models.Model):
    image               = models.ImageField(upload_to=upload_location, null=False)
    post                = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='post_image', null=False)
    user                = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name='user_post_images', null=False)
    created_at	        = models.DateTimeField(verbose_name='created_at', auto_now_add=True)

class Like(models.Model):
    user                = models.ForeignKey('account.Account', on_delete=models.CASCADE, null=False)
    post                = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='liked_post', null=False)
    value               = models.PositiveIntegerField(null=False)

class Comment(models.Model):
    user                = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name='post_user_comment', null=False)
    post                = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='commented_post', null=False)
    comment             = models.TextField(null=False)
    likes               = models.ManyToManyField('account.Account', through='CommentLike', related_name='post_comment_likes')

class CommentLike(models.Model):
    user                = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name='post_user_comment_like', null=False)
    comment             = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='liked_comment', null=False)
    value               = models.PositiveIntegerField(null=False)