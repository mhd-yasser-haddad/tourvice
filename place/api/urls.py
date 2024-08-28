from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from place.api import views
from place.api.views import hello, get_place, list_comments, list_images, not_reviewed_place_list, \
    list_unreviewed_images, list_places_unreviewed_images, get_place_rate, get_comment, list_places_ordered, \
    places_using_hog, search_places_keyword

urlpatterns = [
    # Search place URLs
    path('searchPlaceHog', places_using_hog, name="searchPlaceHog"),
    path('searchPlaceKeyword', search_places_keyword, name="SearchPlaceKeyword"),

    # Place Related URLs
    path('listPlacesOrdered', list_places_ordered, name="ListPlacesOrdered"),
    path('getPlace/<int:place_id>', get_place, name="GetPlace"),
    path('place/<int:id>', views.PlaceDetails.as_view(), name="PlaceCrud"),
    path('placeList', views.PlaceList.as_view(), name="PlaceList"),
    path('notReviewedPlaceList', not_reviewed_place_list, name="NotReviewedPlaceList"),
    # Image Related URLs
    path('listImages/<int:place_id>', views.list_images, name="ListImages"),
    path('listPlacesUnreviewedImages', views.list_places_unreviewed_images, name="ListPlacesUnreviewedImages"),
    path('listUnreviewedImages/<int:place_id>', views.list_unreviewed_images, name="ListUnreviewedImages"),
    path('image/<int:place_id>', views.ImageDetails.as_view(), name="ImageCrud"),
    # Rate Related URLs
    path('getRate/<int:place_id>', get_place_rate, name="GetRate"),
    path('rate/<int:place_id>', views.RateDetails.as_view(), name="RateCrud"),
    # Comment Related URLs
    path('listComments/<int:place_id>', list_comments, name="ListComments"),
    path('getComment/<int:place_id>', get_comment, name="GetComment"),
    path('comment', views.CommentDetails.as_view(), name="CommentCrud"),
    # Comment Like Related URLs
    path('commentlike', views.CommentLikeDetails.as_view(), name="CommentLikeCrud"),
    # Test Routes
    path('hello', hello, name="hello"),
]

urlpatterns = format_suffix_patterns(urlpatterns)
