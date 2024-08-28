from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from post.api import views
from post.api.views import get_post, list_images, get_comment, list_comments, hello, hog, list_posts, \
    list_user_posts, list_place_posts

urlpatterns = [
    # Post Related URLs
    path('listUserPosts/<int:type>', list_user_posts, name="ListUserPosts"),
    path('listPlacePosts/<int:place_id>', list_place_posts, name="ListPlacePosts"),
    path('listPosts/<int:type>', list_posts, name="ListPosts"),
    path('getPost/<int:post_id>', get_post, name="GetPost"),
    path('post/<int:post_id>', views.PostDetails.as_view(), name="PostCrud"),
    # path('postList', views.PostList.as_view(), name="PostList"),
    # Image Related URLs
    path('listImages/<int:post_id>', views.list_images, name="ListImages"),
    path('image/<int:id>', views.ImageDetails.as_view(), name="ImageCrud"),
    # Post Like Related URLs
    path('like/<int:post_id>', views.PostLikeDetails.as_view(), name="PostLikeCrud"),
    # Comment Related URLs
    path('listComments/<int:post_id>', list_comments, name="ListComments"),
    path('getComment/<int:post_id>', get_comment, name="GetComment"),
    path('comment', views.CommentDetails.as_view(), name="CommentCrud"),
    # Comment Like Related URLs
    path('commentlike', views.CommentLikeDetails.as_view(), name="CommentLikeCrud"),
    # Test
    path('hello', hello, name="hello"),
    path('hog', hog, name="hog"),
]

urlpatterns = format_suffix_patterns(urlpatterns)