from rest_framework import exceptions, permissions


class UserPermissions(permissions.BasePermission):

    def has_permission(self, request, view):
        if 'pk' in request.parser_context['kwargs']:
            return request.user.is_authenticated
        else:
            return True
