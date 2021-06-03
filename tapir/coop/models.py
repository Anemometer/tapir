from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tapir.accounts.models import TapirUser, UserInfo
from tapir.coop import pdfs
from tapir.utils.models import DurationModelMixin

COOP_SHARE_PRICE = Decimal(100)
COOP_ENTRY_AMOUNT = Decimal(10)


class ShareOwner(models.Model):
    """ShareOwner represents an owner of a ShareOwnership.

    Usually, this is just a proxy for the associated user. However, it may also be used to
    represent a person or company that does not have their own account.
    """

    user_info = models.OneToOneField(UserInfo, on_delete=models.PROTECT, null=True)

    is_company = models.BooleanField(_("Is company"), blank=False, default=False)
    company_name = models.CharField(_("Company name"), max_length=150, blank=True)
    ratenzahlung = models.BooleanField(verbose_name=_("Ratenzahlung"), default=False)
    is_investing = models.BooleanField(
        _("Is an investing (not active) member"), default=False
    )

    # TODO(Leon Handreke): Remove this temporary field again after the Startnext member integration is done
    # It's only used to send special emails to these members
    is_from_startnext = models.BooleanField(
        _("Comes from Startnext May 2021"), default=False
    )
    startnext_welcome_email_sent = models.BooleanField(default=False)

    # Only for owners that have a user account
    user = models.OneToOneField(
        TapirUser,
        related_name="coop_share_owner",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    def clean(self):
        r = super().clean()
        if self.user_info.is_company and self.user:
            raise ValidationError(
                _("Cannot be a company share owner and have an associated user")
            )
        return r

    def get_absolute_url(self):
        if self.user:
            return self.user.get_absolute_url()
        return reverse("coop:shareowner_detail", args=[self.pk])

    def get_oldest_active_share_ownership(self):
        return self.get_active_share_ownerships().order_by("start_date").first()

    def get_active_share_ownerships(self):
        return self.share_ownerships.active_temporal()

    def num_shares(self) -> int:
        return ShareOwnership.objects.filter(owner=self).count()


class ShareOwnership(DurationModelMixin, models.Model):
    """ShareOwnership represents ownership of a single share."""

    owner = models.ForeignKey(
        ShareOwner,
        related_name="share_ownerships",
        blank=False,
        null=False,
        on_delete=models.PROTECT,
    )


class DraftUser(models.Model):
    user_info = models.OneToOneField(UserInfo, on_delete=models.PROTECT, null=True)

    # For now, make this not editable, as one is the 99%-case. In case somebody wants to buy more shares,
    # we should build a flow for existing users. This also solves the issue of keeping the invoice in sync.
    num_shares = models.IntegerField(
        _("Number of Shares"), blank=False, editable=False, default=1
    )

    attended_welcome_session = models.BooleanField(
        _("Attended Welcome Session"), default=False
    )
    signed_membership_agreement = models.BooleanField(
        _("Signed Beteiligungserklärung"), default=False
    )
    paid_membership_fee = models.BooleanField(_("Paid Membership Fee"), default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse(
            "coop:draftuser_detail",
            args=[
                self.pk,
            ],
        )

    def get_initial_amount(self):
        return self.num_shares * COOP_SHARE_PRICE + COOP_ENTRY_AMOUNT

    def can_create_user(self):
        return self.user_info.email and self.signed_membership_agreement

    def send_startnext_email(self):
        if not self.from_startnext:
            raise Exception("Not from startnext")
        if self.startnext_welcome_email_sent:
            print(
                "Welcome email for %d %s already sent"
                % (self.pk, self.get_display_name())
            )
            return

        mail = EmailMessage(
            subject=_("Willkommen bei SuperCoop eG!"),
            body=render_to_string(
                "coop/email/membership_agreement_startnext.html", {"u": self}
            ),
            from_email="SuperCoop Berlin eG <mitglied@supercoop.de>",
            to=[self.email],
            bcc=["mitglied@supercoop.de"],
            attachments=[
                (
                    "Beteiligungserklärung %s.pdf" % self.get_display_name(),
                    pdfs.get_membership_agreement_pdf(self).write_pdf(),
                    "application/pdf",
                )
            ],
        )
        mail.content_subtype = "html"
        mail.send()

        self.startnext_welcome_email_sent = True
        self.save()
