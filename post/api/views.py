from django.db.models import Q
from rest_framework import status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.authentication import TokenAuthentication

from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.contrib.gis.geos import GEOSGeometry

from operator import itemgetter

import math
from skimage.feature import hog
from skimage import data, exposure
from PIL import Image as HogImage

from post.api.serializers import PostSerializer, ImageSerializer, LikeSerializer, CommentSerializer, CommentLikeSerializer
from post.models import Post, Image, Like, Comment, CommentLike
from place.models import Place


def response(data, messages):
    returnedData = {}
    returnedData['data'] = data
    returnedData['messages'] = messages
    return returnedData


@api_view(['GET'])
@permission_classes([AllowAny])
def list_posts(request, type):
    data = {}
    messages = {}
    allPostsData = []
    user = request.user
    longitude = request.data['longitude']
    latitude = request.data['latitude']

    if type != 0 and type != 1:
        messages['invalid type'] = ['Invalid type, it should be 1 or 0']
        return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

    # <--If post type is visit-->
    if type == 0:
        # <--Getting the closest places in order-->
        placesDetails = []
        placesDistance = []
        placeDistance = {}

        places_ids = []
        places = Place.objects.filter(reviewer_id__isnull=False)
        pnt = GEOSGeometry('SRID=4326;POINT(' + longitude + ' ' + latitude + ')')

        for place in places:
            placeDistance = {}
            placeDistance['id'] = place.id
            pnt2 = GEOSGeometry('SRID=4326;POINT(' + place.longtiude + ' ' + place.latitude + ')')
            placeDistance['dist'] = pnt.distance(pnt2) * 100
            placesDistance.append(placeDistance)

        # Ordering the places depending on the distance
        placesDistance.sort(key=itemgetter('dist'), reverse=False)

        # Getting the places ids
        places_ids = (placeDis['id'] for placeDis in placesDistance)
        # <--Getting the closest places in order-->

        # Getting the posts according the places in order
        for final_place_id in places_ids:
            posts = Post.objects.filter(place_id=final_place_id, post_type=0)
            for post in posts:
                postDetails = {}
                postSerialized = PostSerializer(post)
                postDetails = postSerialized.data

                # Getting the post images
                postImages = Image.objects.filter(post=post).values_list('image', flat=True)

                postDetails['likes'] = Like.objects.filter(post=post, value=1).count()
                postDetails['dislikes'] = Like.objects.filter(post=post, value=2).count()
                postDetails['comments'] = Comment.objects.filter(post=post).count()
                if not user.is_anonymous:
                    try:
                        like = Like.objects.get(post=post, user=user)
                        postDetails['liked'] = like.value
                    except Like.DoesNotExist:
                        postDetails['liked'] = 0
                postDetails['text'] = post.description
                postDetails['imageSource'] = str(post.user.image)
                postDetails['name'] = post.user.name
                postDetails['type'] = post.user.is_reviewer
                postDetails['place'] = post.place.name
                postDetails['place_id'] = post.place.id
                postDetails['postDate'] = post.created_at
                postDetails['imagesSrc'] = postImages

                allPostsData.append(postDetails)

        messages['success'] = ['Data retrieved successfully']
        return Response(response(allPostsData, messages), status=status.HTTP_200_OK)
    # <--If post type is visit-->

    elif type == 1:
        visitedPlaces = Post.objects.filter(user_id=user.id).values_list('place_id', flat=True).distinct()
        notVisitedPlaces = Post.objects.filter(~Q(user_id=user.id)).values_list('place_id', flat=True).distinct()
        visitedPosts = Post.objects.filter(place_id__in=visitedPlaces)
        for post in visitedPosts:
            postDetails = {}
            postSerialized = PostSerializer(post)
            postDetails = postSerialized.data

            # Getting the post images
            postImages = Image.objects.filter(post=post).values_list('image', flat=True)

            postDetails['likes'] = Like.objects.filter(post=post, value=1).count()
            postDetails['dislikes'] = Like.objects.filter(post=post, value=2).count()
            postDetails['comments'] = Comment.objects.filter(post=post).count()
            if not user.is_anonymous:
                try:
                    like = Like.objects.get(post=post, user=user)
                    postDetails['liked'] = like.value
                except Like.DoesNotExist:
                    postDetails['liked'] = 0
            postDetails['text'] = post.description
            postDetails['imageSource'] = str(post.user.image)
            postDetails['name'] = post.user.name
            postDetails['type'] = post.user.is_reviewer
            postDetails['place'] = post.place.name
            postDetails['place_id'] = post.place.id
            postDetails['postDate'] = post.created_at
            postDetails['imagesSrc'] = postImages

            allPostsData.append(postDetails)

        notVisitedPosts = Post.objects.filter(place_id__in=notVisitedPlaces)
        for post in notVisitedPosts:
            postDetails = {}
            postSerialized = PostSerializer(post)
            postDetails = postSerialized.data

            # Getting the post images
            postImages = Image.objects.filter(post=post).values_list('image', flat=True)

            postDetails['likes'] = Like.objects.filter(post=post, value=1).count()
            postDetails['dislikes'] = Like.objects.filter(post=post, value=2).count()
            postDetails['comments'] = Comment.objects.filter(post=post).count()
            if not user.is_anonymous:
                try:
                    like = Like.objects.get(post=post, user=user)
                    postDetails['liked'] = like.value
                except Like.DoesNotExist:
                    postDetails['liked'] = 0
            postDetails['text'] = post.description
            postDetails['imageSource'] = str(post.user.image)
            postDetails['name'] = post.user.name
            postDetails['type'] = post.user.is_reviewer
            postDetails['place'] = post.place.name
            postDetails['place_id'] = post.place.id
            postDetails['postDate'] = post.created_at
            postDetails['imagesSrc'] = postImages

            allPostsData.append(postDetails)

        messages['success'] = ['Data retrieved successfully']
        return Response(response(allPostsData, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_place_posts(request, place_id):
    data = {}
    messages = {}
    user = request.user
    allPostsData = []

    try:
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        messages['not found'] = ['Place does not exist']
        return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

    posts = Post.objects.filter(place=place)
    for post in posts:
        postDetails = {}
        postSerialized = PostSerializer(post)
        postDetails = postSerialized.data

        # Getting the post images
        postImages = Image.objects.filter(post=post).values_list('image', flat=True)

        postDetails['likes'] = Like.objects.filter(post=post, value=1).count()
        postDetails['dislikes'] = Like.objects.filter(post=post, value=2).count()
        postDetails['comments'] = Comment.objects.filter(post=post).count()
        if not user.is_anonymous:
            try:
                like = Like.objects.get(post=post, user=user)
                postDetails['liked'] = like.value
            except Like.DoesNotExist:
                postDetails['liked'] = 0
        postDetails['text'] = post.description
        postDetails['imageSource'] = str(post.user.image)
        postDetails['name'] = post.user.name
        postDetails['type'] = post.user.is_reviewer
        postDetails['place'] = post.place.name
        postDetails['place_id'] = post.place.id
        postDetails['postDate'] = post.created_at
        postDetails['imagesSrc'] = postImages

        allPostsData.append(postDetails)

    messages['success'] = ['Data retrieved successfully']
    return Response(response(allPostsData, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_posts(request, type):
    data = {}
    messages = {}
    allPostsData = []
    user = request.user

    if type != 0 and type != 1:
        messages['invalid type'] = ['Invalid type, it should be 1 or 0']
        return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

    posts = Post.objects.filter(post_type=type, user=user)
    for post in posts:
        postDetails = {}
        postSerialized = PostSerializer(post)
        postDetails = postSerialized.data

        # Getting the post images
        postImages = Image.objects.filter(post=post).values_list('image', flat=True)

        postDetails['likes'] = Like.objects.filter(post=post, value=1).count()
        postDetails['dislikes'] = Like.objects.filter(post=post, value=2).count()
        postDetails['comments'] = Comment.objects.filter(post=post).count()
        if not user.is_anonymous:
            try:
                like = Like.objects.get(post=post, user=user)
                postDetails['liked'] = like.value
            except Like.DoesNotExist:
                postDetails['liked'] = 0
        postDetails['text'] = post.description
        postDetails['imageSource'] = str(post.user.image)
        postDetails['name'] = post.user.name
        postDetails['type'] = post.user.is_reviewer
        postDetails['place'] = post.place.name
        postDetails['place_id'] = post.place.id
        postDetails['postDate'] = post.created_at
        postDetails['imagesSrc'] = postImages

        allPostsData.append(postDetails)

    messages['success'] = ['Data retrieved successfully']
    return Response(response(allPostsData, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_post(request, post_id):
    data = {}
    messages = {}
    user = request.user
    postDetails = {}

    # Getting the post
    try:
        post = Post.objects.get(id=post_id)
    except:
        messages['not found'] = ['Post not found']
        return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

    postSerialized = PostSerializer(post)
    postDetails = postSerialized.data

    # Getting the post images
    postImages = Image.objects.filter(post=post).values_list('image', flat=True)

    postDetails['likes'] = Like.objects.filter(post=post, value=1).count()
    postDetails['dislikes'] = Like.objects.filter(post=post, value=2).count()
    postDetails['comments'] = Comment.objects.filter(post=post).count()
    if not user.is_anonymous:
        try:
            like = Like.objects.get(post=post, user=user)
            postDetails['liked'] = like.value
        except Like.DoesNotExist:
            postDetails['liked'] = 0
    postDetails['text'] = post.description
    postDetails['imageSource'] = str(post.user.image)
    postDetails['name'] = post.user.name
    postDetails['type'] = post.user.is_reviewer
    postDetails['place'] = post.place.name
    postDetails['place_id'] = post.place.id
    postDetails['postDate'] = post.created_at
    postDetails['imagesSrc'] = postImages

    messages['success'] = ['Data retrieved successfully']
    return Response(response(postDetails, messages), status=status.HTTP_200_OK)


class PostDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id):
        data = {}
        messages = {}
        user = request.user
        place_id = request.data['place_id']

        try:
            place = Place.objects.get(id=place_id)
        except Place.DoesNotExist:
            messages['not found'] = ['Place not found']
            return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

        post = Post(place=place, user=user)

        serializer = PostSerializer(post, request.data)
        if serializer.is_valid():
            serializer.save()

            # Returning the response
            messages['success'] = ['place inserted successfully']
            return Response(response(serializer.data, messages), status=status.HTTP_200_OK)

        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, post_id):
        data = {}
        messages = {}
        user = request.user

        try:
            post = Post.objects.get(id=post_id)
        except Place.DoesNotExist:
            messages['not found'] = ['Post not found']
            return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

        if user.id == post.user.id or user.is_reviewer:
            # Editing on the place
            serializer = PostSerializer(post, request.data)
            if serializer.is_valid():
                # serializer.reviewer_id = user.id
                serializer.save(reviewer_id=user.id)
                messages['success'] = ['place updated successfully']
                data = serializer.data
                return Response(response(data, messages), status=status.HTTP_200_OK)
            else:
                return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        messages['unauthorized'] = ['You can not edit on the post, you are not the owner or a reviewer']
        return Response(response(data, messages), status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_images(request, post_id):
    data = {}
    messages = {}

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        messages['not found'] = ['Post not found']
        return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

    images = Image.objects.filter(post=post)
    imageDetails = []
    for image in images:
        imageData = {}
        serializedImage = ImageSerializer(image)
        imageData = serializedImage.data
        imageDetails.append(imageData)

    data['images'] = imageDetails
    messages['success'] = ['Data retrieved successfully']
    return Response(response(data, messages), status=status.HTTP_200_OK)


class ImageDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        data = {}
        messages = {}
        user = request.user

        try:
            post = Post.objects.get(id=id)
        except Post.DoesNotExist:
            messages['not found'] = ['Post not found']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        if post.user_id != user.id:
            messages['cannot add photo'] = ['This is not your post you cannot add a photo']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        image = Image(user=user, post=post, created_at=str(timezone.now()))
        serializer = ImageSerializer(image, request.data)
        if serializer.is_valid():
            serializer.save()
            # Returning the response
            messages['success'] = ['Image inserted successfully']
            return Response(response(serializer.data, messages), status=status.HTTP_200_OK)

        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        data = {}
        messages = {}
        user = request.user

        try:
            image = Image.objects.get(id=id)
        except Image.DoesNotExist:
            messages['not found'] = ['Image not found']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        if not user.is_reviewer and user.id != image.user.id:
            messages['unauthorized'] = ["You can't edit unreviewed images"]
            return Response(response(data, messages), status=status.HTTP_401_UNAUTHORIZED)

        image.image.delete(save=True)
        image.delete()
        messages['success'] = ['Image deleted successfully']
        return Response(response(data, messages), status=status.HTTP_200_OK)


class PostLikeDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id):
        data = {}
        messages = {}
        user = request.user

        # Checking if the post exists
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            messages['not found'] = ['The post does not exist']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        # Checking on the post like from the user
        try:
            postLike = Like.objects.get(post=post, user=user)
            new = False
        except Like.DoesNotExist:
            postLike = Like(post=post, user=user)
            new = True

        serializer = LikeSerializer(postLike, request.data)
        if serializer.is_valid():
            if request.data['value'] == '0' and postLike.id is not None:
                postLike.delete()
            elif request.data['value'] != '0':
                serializer.save()
                data = serializer.data

            # Returning the response
            if new:
                messages['success'] = ['Post like added successfully']
            else:
                messages['success'] = ['Post like updated successfully']
            return Response(response(data, messages), status=status.HTTP_201_CREATED)

        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_comments(request, post_id):
    data = {}
    messages = {}
    user = request.user

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        messages['not found'] = ['The post does not exist']
        return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

    comments = Comment.objects.filter(post=post)
    commentsDetails = []
    for comment in comments:
        commentDetails = {}
        likes = 0
        dislikes = 0
        # Getting all the likes and dislikes for a comment
        commentLikes = CommentLike.objects.filter(comment=comment)
        for commentLike in commentLikes:
            if commentLike.value == 1:
                likes += 1
            elif commentLike.value == 2:
                dislikes += 1

        # knowing if the user liked the comment or not
        if not user.is_anonymous:
            try:
                commentUserLike = CommentLike.objects.get(comment=comment, user=user)
                commentDetails['liked'] = commentUserLike.value
            except CommentLike.DoesNotExist:
                commentDetails['liked'] = 0

        # Gathering the data for the comment
        commentDetails['id'] = comment.id
        commentDetails['name'] = comment.user.name
        commentDetails['type'] = comment.user.is_reviewer
        commentDetails['text'] = comment.comment
        commentDetails['imageSource'] = str(comment.user.image)
        commentDetails['likes'] = likes
        commentDetails['dislikes'] = dislikes
        commentDetails['total'] = likes + dislikes
        commentsDetails.append(commentDetails)

    messages['success'] = ['Data retrieved successfully']
    return Response(response(commentsDetails, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_comment(request, post_id):
    data = {}
    messages = {}
    commentDetails = {}
    user = request.user
    likes = 0
    dislikes = 0

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        messages['not found'] = ['post not found, please try again']
        return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

    comments = Comment.objects.filter(post=post)
    commentsCount = comments.count()
    if commentsCount != 0:
        comment = comments.last()
        commentLikes = CommentLike.objects.filter(comment=comment)
        for commentLike in commentLikes:
            if commentLike.value == 1:
                likes += 1
            elif commentLike.value == 2:
                dislikes += 1

        try:
            commentLikeUser = CommentLike.objects.get(comment=comment, user=user)
            userCommentLike = commentLikeUser.value
        except CommentLike.DoesNotExist:
            userCommentLike = 0

        commentDetails['id'] = comment.id
        commentDetails['name'] = comment.user.name
        commentDetails['type'] = comment.user.is_reviewer
        commentDetails['text'] = comment.comment
        commentDetails['imageSource'] = str(comment.user.image)
        commentDetails['likes'] = likes
        commentDetails['dislikes'] = dislikes
        commentDetails['total'] = likes + dislikes
        commentDetails['liked'] = userCommentLike

    data['commentsNumber'] = commentsCount
    data['comment'] = commentDetails
    messages['success'] = ['Data retrieved successfully']
    return Response(response(data, messages), status=status.HTTP_200_OK)


class CommentDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = {}
        messages = {}
        user = request.user
        post_id = request.data['post_id']

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            messages['not found'] = ['Post not found, please try again']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        comment = Comment(user=user, post=post)
        serializer = CommentSerializer(comment, request.data)
        if serializer.is_valid():
            serializer.save()

            # returning the response
            messages['success'] = ['Comment inserted successfully']
            data = serializer.data
            return Response(response(data, messages), status=status.HTTP_201_CREATED)

        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        data = {}
        messages = {}
        user = request.user
        comment_id = request.data['comment_id']

        try:
            comment = Comment.objects.get(id=comment_id, user=user)
        except Comment.DoesNotExist:
            messages['not found'] = ['The comment does not exist, or you can not edit it']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        serializer = CommentSerializer(comment, request.data)
        if serializer.is_valid():
            serializer.save()

            # returning the response
            messages['success'] = ['Comment updated successfully']
            data = serializer.data
            return Response(response(data, messages), status=status.HTTP_200_OK)

        # response['messages'] = serializer.errors
        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        data = {}
        messages = {}
        user = request.user
        comment_id = request.data['comment_id']

        if user.is_reviewer:
            try:
                comment = Comment.objects.get(id=comment_id)
            except Comment.DoesNotExist:
                messages['not found'] = ['The comment does not exist']
                return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                comment = Comment.objects.get(id=comment_id, user=user)
            except Comment.DoesNotExist:
                messages['not found'] = ['The comment does not exist, or you can not delete it']
                return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        comment.delete()
        messages['success'] = ['Comment deleted successfully']
        return Response(response(data, messages), status=status.HTTP_200_OK)


class CommentLikeDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = {}
        messages = {}
        user = request.user
        comment_id = request.data['comment_id']

        # Checking if the comment exists
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            messages['not found'] = ['The comment does not exist']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        # Checking on the comment like from the user
        try:
            commentLike = CommentLike.objects.get(comment=comment, user=user)
            new = False
        except CommentLike.DoesNotExist:
            commentLike = CommentLike(comment=comment, user=user)
            new = True

        serializer = CommentLikeSerializer(commentLike, request.data)
        if serializer.is_valid():
            if request.data['value'] == '0' and commentLike is not None:
                commentLike.delete()
            elif request.data['value'] != '0':
                serializer.save()
                data = serializer.data

            # Returning the response
            if new:
                messages['success'] = ['Comment like added successfully']
            else:
                messages['success'] = ['Comment like updated successfully']
            return Response(response(data, messages), status=status.HTTP_201_CREATED)

        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def hello(request):
    messages = {}
    data = {}
    pnt = GEOSGeometry('SRID=4326;POINT(49.243824 -121.887340)')
    pnt2 = GEOSGeometry('SRID=4326;POINT(49.235347 -121.92532)')

    data['dis'] = pnt.distance(pnt2) * 100
    return Response(response(data, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def hog(request):
    messages= {}
    data = {}
    hog = 0

    # First Image Process
    image1 = HogImage.open('../../resources/media_cdn/places/images/Admin/1.jpg')
    newSize = (600, 600)
    image1 = image1.resize(newSize)
    featureVector1, hogImage1 = hog(image1, orientations=8, pixels_per_cell=(16, 16), cells_per_block=(1, 1), visualize=True, multichannel=True)

    # Second Image Process
    image2 = HogImage.open('../../resources/media_cdn/places/images/Admin/2.jpg')
    image2 = image2.resize(newSize)
    featureVector2, hogImage2 = hog(image2, orientations=8, pixels_per_cell=(16, 16), cells_per_block=(1, 1), visualize=True, multichannel=True)

    temp = 0
    total = 0
    for index in range(len(featureVector1)):
        temp = (featureVector1[index] - featureVector2[index]) ** 2
        total += temp

    hog = math.sqrt(total)
    data['hog'] = hog
    return Response(response(data, messages), status=status.HTTP_200_OK)