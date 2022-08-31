from rest_framework import permissions


class UserPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if 'id' in request.parser_context['kwargs']:
            return (request.user.is_authenticated and
                    request.method == 'GET')
        else:
            return False


class RecipePermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS or
                request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
