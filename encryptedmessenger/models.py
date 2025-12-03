from django.contrib.auth.models import AbstractUser
from uuid import uuid4
from django.conf import settings
from django.db import models


class User(AbstractUser):
    pass


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    # ADDED: when set, all the messages of the conversation will be deleted after specific time
    autodestruct_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    # Fields for server side encryption
    alg = models.CharField(max_length=32, default="AES-256-GCM") # encryption algorithm
    ciphertext = models.BinaryField() # output of the encryption
    nonce = models.BinaryField() # random value to make encryption unique
    aad = models.BinaryField(blank=True, null=True) # additional authenticated data (but not encrypted)
    wrapped_dek = models.BinaryField() # data encrypted key
    kek_id = models.CharField(max_length=128) # Key Encryption Key ID
    created_at = models.DateTimeField(auto_now_add=True)

    # Metadata (for values Seen and/or Delivered
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "created_at"])
        ]
        ordering = ["created_at"]