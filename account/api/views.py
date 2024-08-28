from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token

from django.core.mail import BadHeaderError, send_mail
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.crypto import get_random_string
from rest_framework.views import APIView

from account.api.serializers import RegistrationSerializer, UserImageSerializer, UserFileSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def registration_view(request):

    # Calling the serializer for the incoming data
    serializer = RegistrationSerializer(data=request.data)
    data = {}
    response = {}
    messages = {}

    # vaidator responded correctly
    if serializer.is_valid():
        # Generating verification code and sending it
        verificationCode = get_random_string(length=6, allowed_chars='0123456789')
        # try:
        # send_mail('TourVice Verification Code', 'Your Verification code is '+verificationCode, 'tourvice2020@gmail.com', [request.data['email']])
        # except BadHeaderError:
        #     messages['email'] = "Failed to send email"
        #     response['data'] = data
        #     response['messages'] = messages
        #     return Response(response, status=status.HTTP_400_BAD_REQUEST)

        # saving the account
        account = serializer.save(verificationCode=verificationCode)
        data['email'] = account.email
        data['username'] = account.username
        data['name'] = account.name
        data['token'] = Token.objects.get(user=account).key
        data['birthDate'] = '1999-01-06'
        data['gender'] = 'male'
        data['country'] = 'syria'
        response['data'] = data

        messages['success'] = ('User registered successfully',)
        response['messages'] = messages

        # return the data
        return Response(response, status=status.HTTP_200_OK)

    else:
        response['data'] = data
        response['messages'] = serializer.errors

        # return the data
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


# Login Class
class CustomAuthToken(ObtainAuthToken):

    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        # Setting up the response
        data = {}
        response = {}
        messages = {}

        # Checking the user
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})

        if serializer.is_valid():
            # Checking if the is valid or not
            user = serializer.validated_data['user']
            token = Token.objects.get(user=user)

            # Setting the response
            data['token'] = token.key
            data['email'] = user.email
            data['username'] = user.username
            data['name'] = user.name
            data['is_reviewer'] = user.is_reviewer

            messages['success'] = ('Logged in successfully',)

            response['data'] = data
            response['messages'] = messages
            return Response(response, status=status.HTTP_200_OK)
        else:
            response['data'] = data
            response['messages'] = serializer.errors
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


# User Info
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    response = {}
    data = {}
    messages = {}
    user = request.user

    response['data'] = data
    response['messages'] = messages
    return Response(response, status=status.HTTP_200_OK)


class UserImageDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = {}
        data = {}
        messages = {}
        user = request.user

        serializer = UserImageSerializer(user, request.data)
        if serializer.is_valid():
            serializer.save()
            # Returning the response
            messages['success'] = ['Image inserted successfully']
            response['data'] = serializer.data
            response['messages'] = messages
            return Response(response, status=status.HTTP_200_OK)

        response['data'] = data
        response['messages'] = serializer.errors
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class UserFileDetails(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = {}
        data = {}
        messages = {}
        user = request.user

        serializer = UserFileSerializer(user, request.data)
        if serializer.is_valid():
            serializer.save()
            # Returning the response
            messages['success'] = ['File inserted successfully']
            response['data'] = serializer.data
            response['messages'] = messages
            return Response(response, status=status.HTTP_200_OK)

        response['data'] = data
        response['messages'] = serializer.errors
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
