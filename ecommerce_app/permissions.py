# permissions.py
from rest_framework.permissions import BasePermission
from rest_framework import permissions

class IsSuperuserOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser or (request.user.is_authenticated and request.user.is_staff)


class IsCartOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.cart.user == request.user


