from django.db import models


def upload_location(instance, filename):
    file_path = 'places/images/{username}/{created_at}-{filename}'.format(
        username=str(instance.user.name), filename=filename, created_at=instance.created_at
    )
    return file_path


class Place(models.Model):
    name                = models.CharField(max_length=255, unique=False, null=False)
    description         = models.TextField(unique=False, null=False)
    longtiude	        = models.CharField(max_length=50, unique=False, null=False)
    latitude	        = models.CharField(max_length=50, unique=False, null=False)
    user                = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name="place_user", null=False)
    reviewer            = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name="reviewer", null=True)
    created_at	        = models.DateTimeField(verbose_name='created_at', auto_now_add=True)
    rates               = models.ManyToManyField('account.Account', through='Rate', related_name='place_rates')
    comments            = models.ManyToManyField('account.Account', through='Comment', related_name='place_comments')

    def __str__(self):
        return self.name

class Image(models.Model):
    image               = models.ImageField(upload_to=upload_location, null=False)
    default             = models.BooleanField(default=True)
    place               = models.ForeignKey('Place', on_delete=models.CASCADE, related_name='place_image', null=False)
    user                = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name='user_place_images', null=False)
    reviewer            = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name="image_reviewer", null=True)
    created_at	        = models.DateTimeField(verbose_name='created_at', auto_now_add=True)

class Rate(models.Model):
    user = models.ForeignKey('account.Account', on_delete=models.CASCADE, null=False)
    place = models.ForeignKey('Place', on_delete=models.CASCADE, related_name='rated_place', null=False)
    rate = models.PositiveIntegerField(null=False)

class Comment(models.Model):
    user = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name='place_user_comment', null=False)
    place = models.ForeignKey('Place', on_delete=models.CASCADE, related_name='commented_place', null=False)
    comment = models.TextField(null=False)
    likes = models.ManyToManyField('account.Account', through='CommentLike', related_name='place_comment_likes')

class CommentLike(models.Model):
    user = models.ForeignKey('account.Account', on_delete=models.CASCADE, related_name='place_user_comment_like', null=False)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='liked_comment', null=False)
    value = models.PositiveIntegerField(null=False)


