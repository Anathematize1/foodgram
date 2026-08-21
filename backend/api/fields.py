"""Кастомные поля сериализаторов."""
import base64
import binascii
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Поле для загрузки изображения, закодированного в Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format_str, imgstr = data.split(';base64,')
                ext = format_str.split('/')[-1]
                if ext == 'jpeg':
                    ext = 'jpg'
                decoded = base64.b64decode(imgstr)
            except (ValueError, TypeError, binascii.Error):
                raise serializers.ValidationError(
                    'Загрузите корректное изображение в формате Base64.',
                )
            data = ContentFile(decoded, name=f'{uuid.uuid4()}.{ext}')
        return super().to_internal_value(data)
