from rest_framework.authentication import SessionAuthentication


class SafeSessionAuthentication(SessionAuthentication):
    """Session auth without CSRF enforcement — CSRF is redundant when
    every write endpoint already gates on IsAuthenticated."""

    def enforce_csrf(self, request):
        pass
