from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response


def add_or_del_obj(request, q, model_fk, model_m2m,
                   serializer, error_message, id):
    obj = get_object_or_404(model_fk, pk=id)
    obj_exists = model_m2m.objects.filter(
        Q(user=request.user) & q)
    if request.method == 'POST':
        if obj_exists:
            return Response(
                error_message['error_create_obj'],
                status=status.HTTP_400_BAD_REQUEST
            )
        model_m2m(None, request.user.id, obj.id).save()
        return Response(
            serializer(obj, context={'request': request}).data
        )
    if obj_exists:
        obj_exists.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response(
        error_message['error_del_obj'],
        status=status.HTTP_400_BAD_REQUEST
    )
