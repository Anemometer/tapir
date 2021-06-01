from django.test import tag
from django.urls import reverse

from tapir.coop.tests.test_applicant_register import ApplicantTestBase
from django.test.testcases import SerializeMixin

from tapir.utils.json_user import JsonUser
from tapir.utils.user_utils import UserUtils


class ApplicantToTapirUserMixin(SerializeMixin):
    lockfile = __file__
    json_file = "test_applicant_create.json"

    def check_share_owner_details(self, user: JsonUser):
        self.go_to_share_owner_detail_page(user)
        self.wait_until_element_present_by_id("share_owner_detail_card")

        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_display_name").text,
            user.get_display_name(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_status").text,
            "Active Member",
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_email").text,
            user.email,
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_birthdate").text,
            user.get_date_of_birth_display(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_address").text,
            user.get_display_address(),
        )
        self.assertEqual(
            self.selenium.find_element_by_id("share_owner_num_shares").text,
            "1",
        )


class TestApplicantCreate(ApplicantTestBase, ApplicantToTapirUserMixin):
    @tag("selenium")
    def test_applicant_create(self):
        # A coop member creates an Applicant (for example at the Welcome desk)
        self.selenium.get(self.URL_BASE)
        self.login_as_admin()
        self.selenium.get(self.URL_BASE + reverse("coop:draftuser_create"))

        user = self.get_test_user(self.json_file)
        self.fill_draftuser_form(user)
        self.wait_until_element_present_by_id("draft_user_detail_card")
        self.check_draftuser_details(user)


class TestCreateShareOwnerFromApplicant(ApplicantTestBase, ApplicantToTapirUserMixin):
    @tag("selenium")
    def test_applicant_to_share_owner(self):
        # A coop member transforms a draft user into a share owner (not an active member yet)
        self.selenium.get(self.URL_BASE)
        self.login_as_admin()

        user = self.get_test_user(self.json_file)
        self.go_to_applicant_detail_page(user)
        self.selenium.find_element_by_id(
            "button_marker_membership_agreement_signed"
        ).click()
        self.wait_until_element_present_by_id("create_member_button")
        self.selenium.find_element_by_id("create_member_button").click()
        self.check_share_owner_details(user)


class TestEditShareOwnerInfos(ApplicantTestBase, ApplicantToTapirUserMixin):
    @tag("selenium")
    def test_edit_share_owner(self):
        # A coop member edits the name of a share owner
        self.login_as_admin()

        user = self.get_test_user(self.json_file)
        name_before = user.first_name
        user.first_name = "an edited first name"
        self.edit_share_owner_name(user)
        self.check_share_owner_details(user)

        # Set the username back to what it was for the following tests
        user.first_name = name_before
        self.edit_share_owner_name(user)

    def edit_share_owner_name(self, user: JsonUser):
        self.go_to_share_owner_detail_page(user)
        self.selenium.find_element_by_id("edit_share_owner_button").click()

        first_name_field = self.selenium.find_element_by_id("id_first_name")
        first_name_field.clear()
        first_name_field.send_keys(user.first_name)
        self.selenium.find_element_by_xpath('//button[@type="submit"]').click()
        self.wait_until_element_present_by_id("share_owner_detail_card")


class TestCreateMemberFromShareOwner(ApplicantTestBase, ApplicantToTapirUserMixin):
    @tag("selenium")
    def test_create_member_from_share_owner(self):
        self.login_as_admin()
        user = self.get_test_user(self.json_file)
        self.go_to_share_owner_detail_page(user)
        self.selenium.find_element_by_id("create_member_button").click()
