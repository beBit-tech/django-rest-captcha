from uuid import uuid4
import os
from PIL import Image
from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse
from rest_captcha.serializers import RestCaptchaSerializer
from django.core.cache import cache
from .settings import api_settings
from . import utils

try:
    from cStringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO


class RestCaptchaTests(TestCase):
    def test_views(self):
        result = self.client.post(reverse('rest_captcha')).json()
        assert 'captcha_key' in result
        assert 'captcha_image' in result
        result['captcha_image'].decode('base64')

    def test_validation_valid(self):
        result = self.client.post(reverse('rest_captcha')).json()
        key = result['captcha_key']
        cache.set(key, 'GOOD')

        data = dict(captcha_key=key, captcha_value='GOOD')
        serial = RestCaptchaSerializer(data=data)
        assert serial.is_valid() is True

    def test_validation_second_try(self):
        result = self.client.post(reverse('rest_captcha')).json()
        key = result['captcha_key']
        cache.set(key, 'GOOD')

        data = dict(captcha_key=result['captcha_key'], captcha_value='BAD')
        serial = RestCaptchaSerializer(data=data)
        assert serial.is_valid() is False

        # second try with GOOD VAL
        data = dict(captcha_key=result['captcha_key'], captcha_value='GOOD')
        serial = RestCaptchaSerializer(data=data)
        assert serial.is_valid() is False

    def test_validation_with_broken_keys(self):
        data = dict(captcha_key=str(uuid4()), captcha_value_123='ABCD')
        serial = RestCaptchaSerializer(data=data)
        assert serial.is_valid() is False
        self.assertDictEqual(
            serial.errors, {'captcha_value': ['This field is required.']})

    def test_validation_with_undefined_key(self):
        data = dict(captcha_key=str(uuid4()), captcha_value='ABCD')
        serial = RestCaptchaSerializer(data=data)
        assert serial.is_valid() is False
        self.assertDictEqual(
            serial.errors,
            {'non_field_errors': ['Invalid or expared captcha key']}
        )

    def test_validation_with_broken_value(self):
        result = self.client.post(reverse('rest_captcha')).json()
        data = dict(captcha_key=result['captcha_key'], captcha_value='ABCD')
        serial = RestCaptchaSerializer(data=data)
        assert serial.is_valid() is False
        self.assertDictEqual(
            serial.errors, {'non_field_errors': ['Invalid captcha value']})


@override_settings()
class ImageGenTests(TestCase):
    def test_change_image_size(self):
        result = self.client.post(reverse('rest_captcha')).json()
        image_bytes = result['captcha_image'].decode('base64')
        image = Image.open(StringIO(image_bytes))
        assert image.size == api_settings.CAPTCHA_IMAGE_SIZE

        api_settings.CAPTCHA_IMAGE_SIZE = (251, 144)
        result = self.client.post(reverse('rest_captcha')).json()
        image_bytes = result['captcha_image'].decode('base64')
        image = Image.open(StringIO(image_bytes))
        assert image.size == api_settings.CAPTCHA_IMAGE_SIZE

    def test_image(self):
        api_settings.CAPTCHA_IMAGE_SIZE = (100, 50)
        api_settings.CAPTCHA_LETTER_ROTATION = None
        utils.random_char_challenge = lambda x: 'CAPTCHA'

        result = self.client.post(reverse('rest_captcha')).json()
        image = result['captcha_image'].decode('base64')
        path = os.path.join(os.path.dirname(__file__), 'captcha.png')
        image2 = open(path, 'r').read()
        # with open(path, 'w+') as f:
        #     f.write(image)
        assert image2 == image