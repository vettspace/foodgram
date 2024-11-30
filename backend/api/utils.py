import base64
from django.core.files.base import ContentFile


def get_image_from_base64(base64_string):
    """Преобразование строки base64 в объект файла."""
    try:
        format, imgstr = base64_string.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
    except Exception as e:
        raise ValueError(f'Invalid image format: {str(e)}')
