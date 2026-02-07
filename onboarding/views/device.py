from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import logging

from account.models.devices import UserDevices
from core.helpers.response import success_response, validation_error_response
from onboarding.serializers import DeviceFCMSerializer

logger = logging.getLogger(__name__)


class DeviceFCMVIew(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = DeviceFCMSerializer(data=request.data)
        if serializer.is_valid():

            device_id = serializer.validated_data.get('device_id')
            token = serializer.validated_data.get('token')

            device, _ = UserDevices.objects.get_or_create(
                user=request.user,
                device_id=device_id)
            device.fcm_token = token
            device.active = True
            device.save()

            logger.info(f"Device registered: {device_id}")

            return success_response({'detail': 'Device registered successfully.'})
        return validation_error_response(serializer.errors)
