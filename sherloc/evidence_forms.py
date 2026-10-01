"""Flask-WTF forms for the consultation pages."""
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    FieldList,
    FormField,
    HiddenField,
    RadioField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import InputRequired

from evidence_choices import (
    YES_NO_DEFAULT, PERSON_DEFAULT, LEGAL_DEFAULT, TWO_FACTOR_DEFAULT, YES_NO_UNSURE_CHOICES, YES_NO_CHOICES, PERSON_CHOICES, PWD_CHOICES, LEGAL_CHOICES, DEVICE_TYPE_CHOICES, TWO_FACTOR_CHOICES,
)
from evidence_model import (
    SuspiciousLogins, PasswordCheck, RecoverySettings, TwoFactorSettings, SecurityQuestions, InstallInfo, PermissionInfo, TAQDevices, TAQAccounts, TAQSharing, TAQSmarthome, TAQKids, TAQLegal,
)


########################
###### FORMS ###########
########################

## HELPER FORMS FOR EVERY PAGE
class NotesForm(FlaskForm):
    client_notes = TextAreaField("Client notes")
    consultant_notes = TextAreaField("Consultant notes")

## HELPER FORMS FOR APPS
class PermissionForm(FlaskForm):
    permissions = HiddenField("Permissions")
    access = RadioField(PermissionInfo().questions["access"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    describe = TextAreaField(PermissionInfo().questions["describe"])

# HELPER FORM FOR SCREENSHOTS

class InstallForm(FlaskForm):
    knew_installed = RadioField(InstallInfo().questions["knew_installed"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    installed = RadioField(InstallInfo().questions["installed"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    coerced = RadioField(InstallInfo().questions["coerced"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    #who = TextAreaField("If you were coerced, who coerced you?")

class SpywareAppForm(FlaskForm):
    title = HiddenField("App Name")
    install_form = FormField(InstallForm)
    app_name = HiddenField("App Name")
    appId = HiddenField("App ID")
    flags = HiddenField("Flags")
    application_icon = HiddenField("App Icon")
    app_website = HiddenField("App Website")
    description = HiddenField("Description")
    #descriptionHTML = HiddenField("HTML Description")
    developerwebsite = HiddenField("Developer Website")
    permissions = HiddenField("Permissions")
    subclass = HiddenField("Subclass")
    summary = HiddenField("Summary")
    notes = FormField(NotesForm)

class DualUseAppForm(FlaskForm):
    title = HiddenField("App Name")
    install_info = FormField(InstallForm)
    permissions = FieldList(FormField(PermissionForm))
    app_name = HiddenField("App Name")
    appId = HiddenField("App ID")
    flags = HiddenField("Flags")
    application_icon = HiddenField("App Icon")
    app_website = HiddenField("App Website")
    description = HiddenField("Description")
    #descriptionHTML = HiddenField("HTML Description")
    developerwebsite = HiddenField("Developer Website")
    subclass = HiddenField("Subclass")
    summary = HiddenField("Summary")
    notes = FormField(NotesForm)

## HELPER FORMS FOR ACCOUNTS
class SuspiciousLoginsForm(FlaskForm):
    recognize = RadioField(SuspiciousLogins().questions["recognize"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    describe_logins = TextAreaField(SuspiciousLogins().questions["describe_logins"])
    activity_log = RadioField(SuspiciousLogins().questions["activity_log"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    describe_activity = TextAreaField(SuspiciousLogins().questions["describe_activity"])

class PasswordForm(FlaskForm):
    last_updated = TextAreaField(PasswordCheck().questions["last_updated"])
    know = RadioField(PasswordCheck().questions["know"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    guess = RadioField(PasswordCheck().questions["guess"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    federated = RadioField(PasswordCheck().questions["federated"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    federated_which = TextAreaField(PasswordCheck().questions["federated_which"])
    federated_comp = RadioField(PasswordCheck().questions["federated_comp"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)

class RecoveryForm(FlaskForm):
    phone_present = RadioField(RecoverySettings().questions["phone_present"], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)
    phone = TextAreaField(RecoverySettings().questions["phone"])
    phone_access = RadioField(RecoverySettings().questions["phone_access"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    email_present = RadioField(RecoverySettings().questions["email_present"], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)
    email = TextAreaField(RecoverySettings().questions["email"])
    email_access = RadioField(RecoverySettings().questions["email_access"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)

class TwoFactorForm(FlaskForm):
    enabled = RadioField(TwoFactorSettings().questions["enabled"], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)
    second_factor_type = SelectMultipleField(TwoFactorSettings().questions["second_factor_type"], choices=TWO_FACTOR_CHOICES, default=TWO_FACTOR_DEFAULT)
    describe = TextAreaField(TwoFactorSettings().questions["describe"])
    second_factor_access = RadioField(TwoFactorSettings().questions["second_factor_access"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)

class SecurityQForm(FlaskForm):
    present = RadioField(SecurityQuestions().questions["present"], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)
    know = RadioField(SecurityQuestions().questions["know"], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    which = TextAreaField(SecurityQuestions().questions["which"])

class AccountInfoForm(FlaskForm):
    username = TextAreaField("Username")
    account_platform = TextAreaField("Platform")
    suspicious_logins = FormField(SuspiciousLoginsForm)
    password_check = FormField(PasswordForm)
    recovery_settings = FormField(RecoveryForm)
    two_factor_settings = FormField(TwoFactorForm)
    security_questions = FormField(SecurityQForm)
    notes = FormField(NotesForm)

class AppSelectForm(FlaskForm):
    title = HiddenField("App Name")
    appId = HiddenField("App ID")
    flags = HiddenField("Flags")
    app_name = HiddenField("App Name")
    #application_icon = HiddenField("App Icon")
    app_website = HiddenField("App Website")
    #description = HiddenField("Description")
    #descriptionHTML = HiddenField("HTML Description")
    #developerwebsite = HiddenField("Developer Website")
    #permission_info = HiddenField(FormField(PermissionForm))
    #subclass = HiddenField("Subclass")
    #summary = HiddenField("Summary")
    investigate = BooleanField("Check this app?")

## INDIVIDUAL PAGES
class StartForm(FlaskForm):
    title = "Device To Be Scanned"
    device_nickname = StringField('Device nickname', validators=[InputRequired()])
    device_type = RadioField('Device type', choices=DEVICE_TYPE_CHOICES, validators=[InputRequired()])
    submit = SubmitField("Scan Device")
    manualadd = SubmitField("Select apps manually")

class ScanForm(FlaskForm):
    title = "Scan Instructions"
    submit = SubmitField("Scan")

class SpywareForm(FlaskForm):
    title = "Step 1: Spyware Check"
    spyware_apps = FieldList(FormField(SpywareAppForm))
    submit = SubmitField("Continue")

class DualUseForm(FlaskForm):
    title = "Step 2: Dual Use App Check"
    dual_use_apps = FieldList(FormField(DualUseAppForm))
    submit = SubmitField("Continue")

class SingleAppCheckForm(FlaskForm):
    title = HiddenField("App Name")
    install_info = FormField(InstallForm)
    permission_info = FormField(PermissionForm)
    appId = HiddenField("App ID")
    flags = HiddenField("Flags")
    application_icon = HiddenField("App Icon")
    app_website = HiddenField("App Website")
    description = HiddenField("Description")
    descriptionHTML = HiddenField("HTML Description")
    developerwebsite = HiddenField("Developer Website")
    subclass = HiddenField("Subclass")
    summary = HiddenField("Summary")
    investigate = HiddenField("Investigate?")
    notes = FormField(NotesForm)

class AppInvestigationForm(FlaskForm):
    title = "App Investigations"
    selected_apps = FieldList(FormField(SingleAppCheckForm))
    submit = SubmitField("Save Investigation")

class AccountCompromiseForm(FlaskForm):
    title = "Account Compromise Check"
    platform = StringField('Platform', validators=[InputRequired()])
    username = StringField('Username', validators=[InputRequired()])
    suspicious_logins = FormField(SuspiciousLoginsForm)
    password_check = FormField(PasswordForm)
    recovery_settings = FormField(RecoveryForm)
    two_factor_settings = FormField(TwoFactorForm)
    security_questions = FormField(SecurityQForm)
    notes = FormField(NotesForm)
    submit = SubmitField("Save")

class AppSelectPageForm(FlaskForm):
    title = "Select Apps to Investigate"
    apps = FieldList(FormField(AppSelectForm))
    submit = SubmitField("Select")

class ManualAppSelectForm(FlaskForm):
    app_name = StringField("App Name")
    spyware = BooleanField("Appears to be a spyware app?")
    dualuse = BooleanField("Appears to be a dual-use app?")

class ManualAddPageForm(FlaskForm):
    title = "Manual App Investigation: Select Apps"
    device_nickname = StringField("Device Nickname", validators=[InputRequired()])
    device_version = StringField("Device Version")
    device_model = StringField("Device Model", validators=[InputRequired()])
    device_manufacturer = StringField("Device Manufacturer")
    device_serial = StringField("Device Serial Number")
    is_rooted = RadioField("Is the device rooted?", choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    rooted_reasons = TextAreaField("Reasons rooting is suspected (if applicable).")
    apps = FieldList(FormField(ManualAppSelectForm))
    addline = SubmitField("Add a new app")
    submit = SubmitField("Submit")

    def update_self(self):
        # read the data in the form
        read_form_data = self.data

        # modify the data as you see fit:
        updated_list = read_form_data['apps']
        if read_form_data['addline']:
            updated_list.append({})
        read_form_data['apps'] = updated_list

        # reload the form from the modified data
        self.__init__(formdata=None, **read_form_data)
        self.validate()  # the errors on validation are cancelled in the line above

class ScreenshotEditForm(FlaskForm):
    fname = StringField("Filename")
    delete = BooleanField("Delete")

class MultScreenshotEditForm(FlaskForm):
    title = "Screenshot Edit Form"
    root_screenshots = FieldList(FormField(ScreenshotEditForm))
    app_screenshots = FieldList(FormField(ScreenshotEditForm))
    acct_screenshots = FieldList(FormField(ScreenshotEditForm))
    submit = SubmitField("Delete Selected Screenshots")

### TAQ Forms
class TAQDeviceCompForm(FlaskForm):
    title = "Device Compromise Indicators"
    live_together = RadioField(
        TAQDevices().questions['live_together'], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)
    purchase_device = RadioField(
        TAQDevices().questions['purchase_device'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    purchase_device_which = TextAreaField(TAQDevices().questions['purchase_device_which'])
    physical_access = RadioField(
        TAQDevices().questions['physical_access'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    physical_access_which = TextAreaField(TAQDevices().questions['physical_access_which'])
    device_pin = RadioField(
        TAQDevices().questions['device_pin'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)

class TAQAccountsForm(FlaskForm):
    title = "Account and Password Management"
    pwd_mgmt = SelectMultipleField(TAQAccounts().questions['pwd_mgmt'], choices=PWD_CHOICES)
    pwd_mgmt_describe = TextAreaField(TAQAccounts().questions['pwd_mgmt_describe'])
    pwd_comp = RadioField(
        TAQAccounts().questions['pwd_comp'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    pwd_comp_which = TextAreaField(TAQAccounts().questions['pwd_comp_which'])

class TAQSharingForm(FlaskForm):
    title = "Account Sharing"
    share_phone_plan = RadioField(
        TAQSharing().questions['share_phone_plan'], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)
    phone_plan_admin = SelectMultipleField(
        TAQSharing().questions['phone_plan_admin'], choices=PERSON_CHOICES, default=PERSON_DEFAULT)
    share_accounts = RadioField(
        TAQSharing().questions['share_accounts'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    share_which = TextAreaField(TAQSharing().questions['share_which'])

class TAQSmartHomeForm(FlaskForm):
    title = "Smart Home Devices"
    smart_home = RadioField(
        TAQSmarthome().questions['smart_home'], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)
    smart_home_setup = SelectMultipleField(
        TAQSmarthome().questions['smart_home_setup'], choices=PERSON_CHOICES, default=PERSON_DEFAULT)
    smart_home_access = RadioField(
        TAQSmarthome().questions['smart_home_access'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    smart_home_acct_sharing = RadioField(
        TAQSmarthome().questions['smart_home_acct_sharing'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    smart_home_acct_linking = RadioField(
        TAQSmarthome().questions['smart_home_acct_linking'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)

class TAQKidsForm(FlaskForm):
    title = "Children's Devices"
    custody = RadioField(
        TAQKids().questions['custody'], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)
    child_phys_access = RadioField(
        TAQKids().questions['child_phys_access'], choices=YES_NO_UNSURE_CHOICES, default=YES_NO_DEFAULT)
    child_phone_plan = RadioField(
        TAQKids().questions['child_phone_plan'], choices=YES_NO_CHOICES, default=YES_NO_DEFAULT)

class TAQLegalForm(FlaskForm):
    title = "Legal Proceedings"
    legal = SelectMultipleField(
        TAQLegal().questions['legal'], choices=LEGAL_CHOICES, default=LEGAL_DEFAULT)

class TAQForm(FlaskForm):
    title = "Technology Assessment Questionnaire (TAQ)"
    marked_done = BooleanField("Mark as complete")
    devices = FormField(TAQDeviceCompForm)
    accounts = FormField(TAQAccountsForm)
    sharing = FormField(TAQSharingForm)
    smarthome = FormField(TAQSmartHomeForm)
    kids = FormField(TAQKidsForm)
    legal = FormField(TAQLegalForm)
    submit = SubmitField("Save TAQ")

class HomepageNoteForm(FlaskForm):
    title = "Overall Consultation Notes"
    consultant_notes = TextAreaField("Consultant Notes")
    client_notes = TextAreaField("Client Notes")
    client_name = StringField("Client Name")
    submit = SubmitField("Save Notes")
    generate_printout = SubmitField("Generate Evidentiary Document")
