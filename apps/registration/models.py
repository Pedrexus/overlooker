from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, Permission
from django.core.mail import send_mail
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    fullname = models.CharField(_('full name'), max_length=100, blank=False)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)

    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)

    # TODO: usar s3 bucket para upload de imagens.
    # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["fullname"]

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """Returns the full name"""
        return self.fullname

    def get_short_name(self):
        """Returns the short name for the user."""
        if self.first_name:
            return self.first_name

        try:
            first_name = str(self.fullname).split()[0]
        except IndexError:
            first_name = ''

        return first_name

    def get_username(self):
        return self.email

    def get_user_groups(self):
        return str.join(', ', self.groups.values_list('name', flat=True))

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Sends an email to this User."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
