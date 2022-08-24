from rest_framework import exceptions, permissions


class UserPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if 'pk' in request.parser_context['kwargs']:
            return request.user.is_authenticated
        else:
            return True


class RecipePermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS or
                request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `owner`.
        return obj.author == request.user
