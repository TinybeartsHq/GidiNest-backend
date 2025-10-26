import requests
import base64
from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import six
import uuid



def image_url_to_base64(image_url):
    # Fetch the image from the URL
    response = requests.get(image_url)
    # Ensure the request was successful
    response.raise_for_status()
    # Encode the image content in Base64
    image_base64 = base64.b64encode(response.content).decode('utf-8')
    return image_base64




class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # If it is, decode it
            if 'data:' in data and ';base64,' in data:
                # Strip out the headers from the base64 string
                header, data = data.split(';base64,')

            try:
                # Decode the base64 string
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate a file name and file extension
            file_name = str(uuid.uuid4())[:12]  # 12 characters are more than enough.
            file_extension = self.get_file_extension(file_name, decoded_file)

            # Complete the file name
            complete_file_name = "%s.%s" % (file_name, file_extension)

            # Create a Django file object
            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        # Try to guess the file extension
        import imghdr

        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension

        return extension