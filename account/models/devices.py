from django.db import models
from account.models.users import UserModel
from core.helpers.model import BaseModel


class UserDevices(BaseModel):


    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='user_devices')
    device_id = models.CharField(max_length=255,null=True)
    active = models.BooleanField(default=True)
    device_os =  models.CharField(max_length=255,null=True)
    device_info =  models.CharField(max_length=255,null=True)
    fcm_token = models.TextField(null=True)
 
    def __str__(self):
        return f"User Device for {self.user.username}"
    

    class Meta:
        verbose_name = "User Device"
        verbose_name_plural = "User Devices"
        ordering = ['-created_at']


    