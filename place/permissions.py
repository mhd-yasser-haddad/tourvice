from rest_framework import permissions


class IsReviewer(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.user.is_reviewer is True:
            return True
        else:
            return False
