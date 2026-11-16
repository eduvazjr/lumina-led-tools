from django.contrib.auth import get_user_model

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class ExistingUserSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Restringe o Google a usuarios previamente criados pelo administrador."""

    def authenticate_by_email(self, sociallogin):
        """Aceita somente um usuario ativo e inequivoco para o e-mail verificado."""
        for email_address in sociallogin.email_addresses:
            email = email_address.email
            if not email_address.verified:
                continue
            if not self.can_authenticate_by_email(sociallogin, email):
                continue

            users = list(
                get_user_model().objects.filter(
                    email__iexact=email,
                    is_active=True,
                )[:2]
            )
            if len(users) == 1:
                return users[0], email

        return None

    def is_open_for_signup(self, request, sociallogin):
        return False
