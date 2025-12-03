import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from encryptedmessenger.models import Conversation, Message
from encryptedmessenger.enc_services import decrypt_message, encrypt_message

User = get_user_model()


def _is_member_of_conversation(user, conv: Conversation) -> bool:
    return conv.members.filter(pk=user.pk).exists()


def _autodestruct_if_set(conv: Conversation):
    """
    If autodestruct_at is set and has passed, all messages of specific conversation are deleted.
    """
    if conv.autodestruct_at and timezone.now() >= conv.autodestruct_at:
        Message.objects.filter(conversation=conv).delete()
        conv.autodestruct_at = None
        conv.save(update_fields=["autodestruct_at"])


@ensure_csrf_cookie
@login_required
@require_http_methods(["GET", "POST"])
def conversations_view(request):
    if request.method == "GET":
        conversations = []
        for conv in request.user.conversations.all().order_by("-created_at"):
            conversations.append({
                "id": str(conv.id),
                "title": conv.title,
                "members": list(conv.members.values_list("username",
                                                         flat=True)),  # flat=True returns single values
                "created_at": conv.created_at.isoformat(),
                # autodestruct_at is included here to show countdown to the front-end
                "autodestruct_at": conv.autodestruct_at.isoformat() if conv.autodestruct_at else None
            })
        return JsonResponse({"conversations": conversations})

    # POST
    try:
        payload = json.loads(request.body.decode("utf-8"))
        members_usrn = payload.get("members") or []
        if request.user.username not in members_usrn:
            members_usrn.append(request.user.username)
        members = list(User.objects.filter(username__in=members_usrn))

        # check any usernames that do NOT exist
        existing_usernames = {u.username for u in members}
        invalid_usernames = [u for u in members_usrn if u not in existing_usernames]

        if invalid_usernames:
            return JsonResponse({
                "error": "invalid_usernames",
                "message": f"The following usernames do not exist: {', '.join(invalid_usernames)}"
            },
                status=400
            )
        title = ", ".join(members_usrn)
        conv = Conversation.objects.create(title=title)
        conv.members.set(members)
        return JsonResponse({
            "id": str(conv.id),
            "title": conv.title,
            "members": [u.username for u in members],
            "created_at": conv.created_at.isoformat()
        }, status=201)
    except (json.JSONDecodeError, KeyError):
        return HttpResponseBadRequest("Invalid JSON.")


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def messages_view(request, conversation_id: str):
    conv = get_object_or_404(Conversation, pk=conversation_id)

    if not _is_member_of_conversation(request.user, conv):
        return HttpResponseForbidden("Not a member of this conversation")

    # ADDED: autodestruct messages if set and time has passed
    _autodestruct_if_set(conv)

    if request.method == "GET":
        # Decrypting each message on the server
        out = []
        for m in conv.messages.select_related("sender").all().order_by("created_at"):
            aad = (f"{conv.id}|{m.sender_id}").encode("utf-8")
            try:
                plaintext = decrypt_message(m.ciphertext, m.nonce, aad, m.wrapped_dek)
                text = plaintext.decode("utf-8", errors="replace")
            except Exception:
                text = "Decryption Error"
            out.append({
                "id": str(m.id),
                "sender": m.sender.username,
                "created_at": m.created_at.isoformat(),
                "text": text
            })
        return JsonResponse({"messages": out})

    # POST
    try:
        payload = json.loads(request.body.decode("utf-8"))
        text = payload.get("text", "")
        if not text:
            return HttpResponseBadRequest("Blank text.")
        aad = (f"{conv.id}|{request.user.id}").encode("utf-8")
        blob = encrypt_message(text.encode("utf-8"), aad=aad)
        message = Message.objects.create(
            conversation=conv,
            sender=request.user,
            **blob,
            meta={}
        )
        return JsonResponse({
            "id": str(message.id),
            "sender": request.user.username,
            "created_at": message.created_at.isoformat()
        }, status=201)
    except (json.JSONDecodeError, KeyError):
        return HttpResponseBadRequest("Invalid JSON.")


@login_required
@ensure_csrf_cookie
@require_http_methods(["GET","POST"])
def autodestruct_view(request, conversation_id: str):
    conv = get_object_or_404(Conversation, pk=conversation_id)

    if not _is_member_of_conversation(request.user, conv):
        return HttpResponseForbidden("Not a member of this conversation")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        delay_minutes = int(payload.get("delay_minutes", 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return HttpResponseBadRequest("Invalid JSON or delay time")

    if delay_minutes not in (1, 3, 5):
        return HttpResponseBadRequest("Invalid delay value.")

    conv.autodestruct_at = timezone.now() + timedelta(minutes=delay_minutes)
    conv.save(update_fields=["autodestruct_at"])

    return JsonResponse({
        "status": "set",
        "autodestruct_at": conv.autodestruct_at.isoformat()
    })

