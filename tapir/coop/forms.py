from django import forms
from django.contrib.admin.widgets import AdminDateWidget

from tapir.accounts.forms import UserInfoAdminForm, UserInfoNonAdminForm
from tapir.accounts.models import UserInfo
from tapir.coop.models import ShareOwnership, DraftUser, ShareOwner
from tapir.utils.forms import CombinedFormBase


class CoopShareOwnershipForm(forms.ModelForm):
    class Meta:
        model = ShareOwnership
        fields = (
            "start_date",
            "end_date",
        )

    start_date = forms.DateField(widget=AdminDateWidget())
    end_date = forms.DateField(widget=AdminDateWidget(), required=False)


class DraftUserForm(forms.ModelForm):
    class Meta:
        model = DraftUser
        fields = [
            "attended_welcome_session",
        ]


class DraftUserCreateForm(CombinedFormBase):
    form_classes = [UserInfoAdminForm, DraftUserForm]

    def save(self) -> DraftUser:
        user_info_form = getattr(self, UserInfoAdminForm.__name__.lower())
        user_info: UserInfo = user_info_form.save()
        draft_user_form = getattr(self, DraftUserForm.__name__.lower())
        draft_user: DraftUser = draft_user_form.save()
        draft_user.user_info = user_info
        draft_user.save()
        return draft_user


class DraftUserRegisterForm(CombinedFormBase):
    form_classes = [UserInfoNonAdminForm, DraftUserForm]

    def save(self) -> DraftUser:
        user_info_form: UserInfoNonAdminForm = getattr(
            self, UserInfoNonAdminForm.__name__.lower()
        )
        user_info: UserInfo = user_info_form.save()
        draft_user_form = getattr(self, DraftUserForm.__name__.lower())
        draft_user: DraftUser = draft_user_form.save()
        draft_user.user_info = user_info
        draft_user.save()
        return draft_user


class ShareOwnerForm(forms.ModelForm):
    class Meta:
        model = ShareOwner
        fields = [
            "user_info",
        ]
