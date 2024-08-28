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

from django.utils import timezone
from django.contrib.gis.geos import GEOSGeometry

from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import timezone

from operator import itemgetter

import math
from skimage.feature import _hog
from skimage import data, exposure, feature
from PIL import Image as HogImage

from place.permissions import IsReviewer
from place.api.serializers import PlaceSerializer, ImageSerializer, RateSerializer, CommentSerializer, CommentLikeSerializer
from place.models import Place, Image, Rate, Comment, CommentLike


def response(data, messages):
    returnedData = {}
    returnedData['data'] = data
    returnedData['messages'] = messages
    return returnedData


@api_view(['GET'])
@permission_classes([AllowAny])
def places_using_hog(request):
    messages= {}
    data = {}
    hogValue = 0
    uploadedImage = request.data['image']
    longitude = request.data['longitude']
    latitude = request.data['latitude']
    closePlaces = []

    # Uploaded Image Process
    image1 = HogImage.open(uploadedImage)
    newSize = (256, 128)
    image1 = image1.resize(newSize)
    featureVector1 = _hog.hog(image1, orientations=8, pixels_per_cell=(16, 16), cells_per_block=(1, 1), visualize=False,
                              multichannel=True)

    # Current place point
    pnt = GEOSGeometry('SRID=4326;POINT(' + longitude + ' ' + latitude + ')')

    places = Place.objects.filter(reviewer_id__isnull=False)

    # Getting the places in 4 km radius
    for place in places:
        pnt2 = GEOSGeometry('SRID=4326;POINT(' + place.longtiude + ' ' + place.latitude + ')')
        distance = pnt.distance(pnt2) * 100
        if distance < 4:
            closePlaces.append(place.id)

    # return Response(response(closePlaces, messages), status=status.HTTP_200_OK)

    # Getting the images
    placesHog = []
    for closePlaceID in closePlaces:
        placeImages = Image.objects.filter(place_id=closePlaceID, reviewer_id__isnull=False)
        hogValue = 1000000
        placeHog = {}
        for image in placeImages:
            # Second Image Process
            image2 = HogImage.open('resources/media_cdn/'+str(image.image))
            image2 = image2.resize(newSize)
            featureVector2 = _hog.hog(image2, orientations=8, pixels_per_cell=(16, 16), cells_per_block=(1, 1),
                                      visualize=False, multichannel=True)

            temp = 0
            total = 0
            for index in range(len(featureVector1)):
                temp = (featureVector1[index] - featureVector2[index]) ** 2
                total += temp

            if math.sqrt(total) < hogValue:
                hogValue = math.sqrt(total)
                imageURL = str(image.image)
        placeHog['id'] = closePlaceID
        placeHog['hogValue'] = hogValue
        placeHog['imageURL'] = imageURL
        placesHog.append(placeHog)

    # Ordering the places depending on the Hog value
    placesHog.sort(key=itemgetter('hogValue'), reverse=False)

    # Getting the places ids after hog
    placesIDsAfterHog = (placeHog['id'] for placeHog in placesHog)

    placesDetails = []
    for placeIdAfterHog in placesIDsAfterHog:
        place = Place.objects.get(id=placeIdAfterHog)

        placeDetails = {}
        placeDetails = PlaceSerializer(place).data
        defaultImage = Image.objects.filter(place_id=placeIdAfterHog, default=1).first()
        placeDetails['image'] = str(defaultImage.image)
        placesDetails.append(placeDetails)

    return Response(response(placesDetails, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def calc_dist(long1, long2, lat1, lat2):
    pnt = GEOSGeometry('SRID=4326;POINT('+long1+' '+lat1+')')
    pnt2 = GEOSGeometry('SRID=4326;POINT('+long2+' '+lat2+')')

    return pnt.distance(pnt2) * 100


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_places_keyword(request):
    messages = {}
    placesDetails = []
    keyword = request.data['keyword']

    places = Place.objects.filter(name__contains=keyword)
    for place in places:
        placeDetails = {}
        placeDetails = PlaceSerializer(place).data
        defaultImage = Image.objects.filter(place=place, default=1).first()
        placeDetails['image'] = str(defaultImage.image)
        placesDetails.append(placeDetails)

    messages['success'] = ['Data retrieved successfully']
    return Response(response(placesDetails, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_places_ordered(request):
    data = {}
    messages = {}
    user = request.user
    longitude = request.data['longitude']
    latitude = request.data['latitude']
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

    places = dict([(place.id, place) for place in places])
    sortedPlaces = [places[id] for id in places_ids]

    for sortedPlace in sortedPlaces:
        placeDetails = {}
        placeDetails = PlaceSerializer(sortedPlace).data
        defaultImage = Image.objects.filter(place=sortedPlace, default=1).first()
        placeDetails['image'] = str(defaultImage.image)
        placesDetails.append(placeDetails)

    messages['success'] = ['Data retrieved successfully']
    return Response(response(placesDetails, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_place(request, place_id):
    data = {}
    messages = {}
    placeDetails = {}

    # Getting the place
    try:
        place = Place.objects.get(id=place_id)
    except:
        messages['not found'] = ['Place not found']
        return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

    placeSerialized = PlaceSerializer(place)
    placeDetails = placeSerialized.data

    # Getting the place default image
    defaultImage = Image.objects.filter(place=place, default=1).first()
    if defaultImage is None:
        placeDetails['image'] = False
    else:
        placeDetails['image'] = str(defaultImage.image)

    data['place'] = placeDetails
    messages['success'] = ['Data retrieved successfully']
    return Response(response(data, messages), status=status.HTTP_200_OK)


class PlaceDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        data = {}
        messages = {}
        user = request.user

        if user.is_reviewer:
            place = Place(user=user, reviewer_id=user.id)
        else:
            place = Place(user=user)
        serializer = PlaceSerializer(place, request.data)
        if serializer.is_valid():
            serializer.save()
            # Returning the response
            messages['success'] = ['place inserted successfully']
            return Response(response(serializer.data, messages), status=status.HTTP_200_OK)

        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, id):
        data = {}
        messages = {}
        user = request.user

        if user.is_reviewer:
            try:
                place = Place.objects.get(id=id)
            except Place.DoesNotExist:
                messages['not found'] = ['Place not found']
                return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

            # Editing on the place
            serializer = PlaceSerializer(place, request.data)
            if serializer.is_valid():
                # serializer.reviewer_id = user.id
                serializer.save(reviewer_id=user.id)
                messages['success'] = ['place updated successfully']
                data = serializer.data
                return Response(response(data, messages), status=status.HTTP_200_OK)
            else:
                return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

        messages['unauthorized'] = ['You can not edit on the place, you are not a reviewer']
        return Response(response(data, messages), status=status.HTTP_401_UNAUTHORIZED)

    def delete(self, request, id):
        data = {}
        messages = {}
        user = request.user

        if user.is_reviewer:
            try:
                place = Place.objects.get(id=id)
            except Place.DoesNotExist:
                messages['not found'] = ['Place not found']
                return Response(response(data, messages), status=status.HTTP_404_NOT_FOUND)

            place.delete()
            messages['success'] = ['place deleted successfully']
            return Response(response(data, messages), status=status.HTTP_200_OK)

        messages['unauthorized'] = ['You can not edit on the place, you are not a reviewer']
        return Response(response(data, messages), status=status.HTTP_401_UNAUTHORIZED)


class PlaceList(ListAPIView):
    queryset = Place.objects.filter(reviewer_id__isnull=False)
    serializer_class = PlaceSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def not_reviewed_place_list(request):
    data = {}
    messages = {}
    placesDetails = []

    places = Place.objects.filter(reviewer_id__isnull=True)
    for place in places:
        placeDetails = {}
        placeDetails['id'] = place.id
        placeDetails['name'] = place.name
        placeDetails['description'] = place.description
        placeDetails['longtiude'] = place.longtiude
        placeDetails['latitude'] = place.latitude
        defaultImage = Image.objects.filter(place=place, default=1).first()
        if defaultImage is None:
            placeDetails['image'] = False
        else:
            placeDetails['image'] = str(defaultImage.image)
        placesDetails.append(placeDetails)

    messages['success'] = ['Data retrieved successfully']
    return Response(response(placesDetails, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_images(request, place_id):
    data = {}
    messages = {}

    try:
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        messages['not found'] = ['Place not found']
        return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

    images = Image.objects.filter(place=place, reviewer_id__isnull=False)
    imageDetails = []
    for image in images:
        imageData = {}
        # serializedImage = ImageSerializer(image)
        # imageData = serializedImage.data
        imageData['id'] = image.id
        imageData['image'] = str(image.image)
        imageData['user'] = image.user.name
        imageDetails.append(imageData)

    data['images'] = imageDetails
    messages['success'] = ['Data retrieved successfully']
    return Response(response(data, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_places_unreviewed_images(request):
    data = {}
    messages = {}
    places = []
    user = request.user

    if not user.is_reviewer:
        messages['unauthorized'] = ["You can't see the unreviewed images"]
        return Response(response(data, messages), status=status.HTTP_401_UNAUTHORIZED)

    places_ids = Image.objects.filter(reviewer_id__isnull=True).values_list('place_id', flat=True).distinct()

    for place_id in places_ids:
        placeDetails = {}
        place = Place.objects.get(id=place_id)
        placeDetails['id'] = place_id
        placeDetails['name'] = place.name
        placeDetails['description'] = place.description
        placeDetails['longtiude'] = place.longtiude
        placeDetails['latitude'] = place.latitude
        # Getting the place default image
        defaultImage = Image.objects.filter(place=place, default=1).first()
        if defaultImage is None:
            placeDetails['image'] = False
        else:
            placeDetails['image'] = str(defaultImage.image)

        places.append(placeDetails)
    return Response(response(places, messages), status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_unreviewed_images(request, place_id):
    data = {}
    messages = {}
    user = request.user

    if not user.is_reviewer:
        messages['unauthorized'] = ["You can't see the unreviewed images"]
        return Response(response(data, messages), status=status.HTTP_401_UNAUTHORIZED)

    try:
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        messages['not found'] = ['Place not found']
        return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

    images = Image.objects.filter(place=place, reviewer_id__isnull=True)
    imageDetails = []
    for image in images:
        imageData = {}
        serializedImage = ImageSerializer(image)
        imageData = serializedImage.data
        imageData['id'] = image.id
        imageData['user'] = image.user.name
        imageDetails.append(imageData)

    data['images'] = imageDetails
    messages['success'] = ['Data retrieved successfully']
    return Response(response(data, messages), status=status.HTTP_200_OK)


class ImageDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, place_id):
        data = {}
        messages = {}
        user = request.user

        try:
            place = Place.objects.get(id=place_id)
        except Place.DoesNotExist:
            messages['not found'] = ['Place not found']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        defaultImagesCount = Image.objects.filter(place=place, default=1).count()
        if defaultImagesCount > 0:
            default = 0
        else:
            default = 1

        if user.is_reviewer:
            image = Image(user=user, place=place, default=default, created_at=str(timezone.now()), reviewer_id=user.id)
        else:
            image = Image(user=user, place=place, default=default, created_at=str(timezone.now()))

        serializer = ImageSerializer(image, request.data)
        if serializer.is_valid():
            serializer.save()
            # Returning the response
            messages['success'] = ['Image inserted successfully']
            return Response(response(serializer.data, messages), status=status.HTTP_200_OK)

        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, place_id):
        data = {}
        messages = {}
        user = request.user
        reviewing_value = int(request.data['value'])
        image_id = request.data['image_id']

        if not user.is_reviewer:
            messages['unauthorized'] = ["You can't edit unreviewed images"]
            return Response(response(data, messages), status=status.HTTP_401_UNAUTHORIZED)

        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            messages['not found'] = ['Image not found']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        if reviewing_value == 1:
            data['image'] = image.image
            serializer = ImageSerializer(image, data)
            if serializer.is_valid():
                serializer.save(reviewer_id=user.id)
                messages['success'] = ['Image accepted successfully']
                return Response(response(serializer.data, messages), status=status.HTTP_200_OK)
            else:
                return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)
        elif reviewing_value == 0:
            image.image.delete(save=True)
            image.delete()
            messages['success'] = ['Image deleted successfully']
            return Response(response(data, messages), status=status.HTTP_200_OK)
        else:
            messages['invalid data'] = ['The value should be 0 or 1']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_place_rate(request, place_id):
    data = {}
    messages = {}
    user = request.user
    count = 0
    avg = 0

    try:
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        messages['not found'] = ['Place not found, please try again']
        return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

    if not user.is_anonymous:
        try:
            rate = Rate.objects.get(place=place, user=user)
            userRate = rate.rate
        except Rate.DoesNotExist:
            userRate = 0
        data['userRate'] = userRate

    rates = Rate.objects.filter(place=place)
    ratesCount = rates.count()
    for rate in rates:
        avg += rate.rate
        count += 1

    if count == 0:
        avg = 0
    else:
        avg = avg / count

    data['totalRate'] = avg
    data['ratesCount'] = ratesCount
    messages['success'] = ['Data retrieved successfully']

    return Response(response(data, messages), status=status.HTTP_200_OK)


class RateDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, place_id):
        data = {}
        messages = {}
        user = request.user

        try:
            place = Place.objects.get(id=place_id)
        except Place.DoesNotExist:
            messages['not found'] = ['Place not found, please try again']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        try:
            rate = Rate.objects.get(user=user, place=place)
            new = False
        except Rate.DoesNotExist:
            rate = Rate(user=user, place=place)
            new = True
        serializer = RateSerializer(rate, request.data)
        if serializer.is_valid():
            serializer.save()

            # Returning the response
            if new:
                messages['success'] = ['Rate inserted successfully']
            else:
                messages['success'] = ['Rate updated successfully']
            data = serializer.data
            return Response(response(data, messages), status=status.HTTP_200_OK)

        # response['messages'] = serializer.errors
        return Response(response(data, serializer.errors), status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_comments(request, place_id):
    data = {}
    messages = {}
    user = request.user

    try:
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        messages['not found'] = ['The place does not exist']
        return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

    comments = Comment.objects.filter(place=place)
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
def get_comment(request, place_id):
    data = {}
    messages = {}
    commentDetails = {}
    user = request.user
    likes = 0
    dislikes = 0

    try:
        place = Place.objects.get(id=place_id)
    except Place.DoesNotExist:
        messages['not found'] = ['place not found, please try again']
        return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

    comments = Comment.objects.filter(place=place)
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
        place_id = request.data['place_id']

        try:
            place = Place.objects.get(id=place_id)
        except Place.DoesNotExist:
            messages['not found'] = ['Place not found, please try again']
            return Response(response(data, messages), status=status.HTTP_400_BAD_REQUEST)

        comment = Comment(user=user, place=place)
        serializer = CommentSerializer(comment, request.data)
        if serializer.is_valid():
            serializer.save()

            # returning the response
            messages['success'] = ['Comment inserted successfully']
            data = serializer.data
            return Response(response(data, messages), status=status.HTTP_201_CREATED)

        # response['messages'] = serializer.errors
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

        if user.is_reviewer == 1:
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
def hello(request):
    response = {}
    response['data'] = 'hello'
    return Response(response, status=status.HTTP_200_OK)
