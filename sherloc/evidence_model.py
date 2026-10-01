"""Data classes for a consultation: scans, apps, accounts, TAQ answers, notes."""
import json
import os
import re
import subprocess
from enum import Enum
from pathlib import Path


class Pages(Enum):
    START = 1
    SCAN = 2
    SPYWARE = 3
    DUALUSE = 4
    ACCOUNTS_USED = 5
    ACCOUNT_COMP = 6

    ### ----------------------------------
### ----------------------------------
### DATA TYPING
### ----------------------------------
### ----------------------------------

### HELPER CLASSES

# Helps create JSON encoding from nested classes
class EvidenceDataEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Path):
            return str(o)
        return o.__dict__

class Dictable:
    def to_dict(self):
        return json.loads(json.dumps(self, cls=EvidenceDataEncoder))

# Base class for nested classes where we'll input data as dict (for ease)
class DictInitClass(Dictable):
    attrs = []

    def __init__(self, datadict=None):
        if datadict is None:
            datadict = dict()
        for k in self.attrs:
            if k in list(datadict.keys()):
                setattr(self, k, datadict[k])
            else:
                setattr(self, k, "")


class AccountSection(DictInitClass):
    screenshot_label = ""
    attrs = ["account_id"]

    def __init__(self, datadict=None):
        if datadict is None:
            datadict = dict()
        super(AccountSection, self).__init__(datadict=datadict)
        self.screenshot_files = list()
        self.screenshot_info = list()

    def set_screenshot_files(self, screenshot_files):
        self.screenshot_files = screenshot_files

    def create_screenshot_info(self, get_metadata=True):
        '''
        Creates screenshot objects for all screenshot files related to this account section.
        '''
        self.screenshot_info = [ScreenshotInfo(
            fname=fname,
            context="account",
            get_metadata=get_metadata
        ) for fname in self.screenshot_files]

        return self.screenshot_info

class SuspiciousLogins(AccountSection):
    questions = {
        'recognize': "Do you see any unrecognized devices that are logged into this account?",
        'describe_logins': "Which devices do you not recognize?",
        'activity_log': "In the login history, do you see any suspicious logins?",
        'describe_activity': "Which logins are suspicious, and why?"
    }
    attrs = AccountSection.attrs + list(questions.keys())
    screenshot_label = "suspicious_logins"

    def generate_risk_report(self):
        '''
        Generate a risk report about suspicious logins. Possible risks:
            - Unrecognized devices
            - Suspicious logins
        '''
        risks = list()

        if self.recognize == 'yes':
            new_risk = Risk(
                risk = "Unrecognized devices",
                description = "There are unrecognized devices currently logged into this account."
            )
            risks.append(new_risk)

        if self.activity_log == 'yes':
            new_risk = Risk(
                risk = "Suspicious logins",
                description = "There are suspicious logins to this account that do not appear to have come from the client."
            )
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report

class PasswordCheck(AccountSection):
    questions = {
        "last_updated": "When did you last update this password (approximately)?",
        "know": "Does the person of concern know the password for this account?",
        "guess": "Do you believe the person of concern could guess the password?",
        "federated": "Do you log into this account using a federated login (e.g., Google, Facebook, Apple)?",
        "federated_which": "What other account do you use to log in?",
        "federated_comp": "Do you believe the person of concern has access to the federated account?",
    }
    attrs = AccountSection.attrs + list(questions.keys())

    def __init__(self, datadict=None):
        if datadict is None:
            datadict = dict()
        super(PasswordCheck, self).__init__(datadict=datadict)

    def generate_risk_report(self):
        '''
        Generate a risk report about password knowledge. Possible risks:
            - Knowledge of passwords
            - Ability to guess password
        '''
        risks = list()

        if self.know == 'yes':
            new_risk = Risk(
                risk = "Password compromise",
                description = "Knowing the password to this account could enable the person of concern to log in. (Note: If two-factor authentication is enabled, they would still need to bypass the second factor.)"
            )
            risks.append(new_risk)

        elif self.guess == 'yes':
            new_risk = Risk(
                risk = "Potential password compromise",
                description = "The client believes the person of concern could guess the password for this account. If they guess correctly, it would enable them to log in. (Note: If two-factor authentication is enabled, they would still need to bypass the second factor.)"
            )
            risks.append(new_risk)

        if self.federated_comp == "yes":
            new_risk = Risk(
                risk = "Compromised federated account",
                description = "By compromising the federated account, the person of concern could log into this account without needing to know the password."
            )
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report

class RecoverySettings(AccountSection):
    questions = {
        'phone_present': "Is there a recovery phone number set for this account?",
        'phone': "What is the recovery phone number?",
        'phone_access': "Do you believe the person of concern has access to the recovery phone number?",
        'email_present': "Is there a recovery email address set for this account?",
        'email': "What is the recovery email address?",
        'email_access': "Do you believe the person of concern has access to this recovery email address?"
    }
    attrs = AccountSection.attrs + list(questions.keys())
    screenshot_label = "recovery_settings"

    def generate_risk_report(self):
        '''
        Generate a risk report about recovery settings. Possible risks:
            - Recovery settings compromised
        '''
        risks = list()

        if self.phone_access == 'yes' or self.email_access == 'yes':
            new_risk = Risk(
                risk = "Compromised recovery information",
                description = "With access to the recovery contact information, someone can access an account without knowing the password using the 'Forgot password' option."
            )
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report

class TwoFactorSettings(AccountSection):
    questions = {
        'enabled': "Is two-factor authentication enabled for this account?",
        'second_factor_type': "What type of two-factor authentication is used?",
        'describe': "Which phone/email/app is set as the second factor?",
        'second_factor_access': "Do you believe the person of concern has access to this second factor?",
    }
    attrs = AccountSection.attrs + list(questions.keys())
    screenshot_label = "two_factor_settings"

    def generate_risk_report(self):
        '''
        Generate a risk report about two factor settings. Possible risks:
            - Two factor not set
            - 2nd factor compromised
        '''
        risks = list()

        if self.second_factor_access == 'yes':
            new_risk = Risk(
                risk = "Compromised second factor",
                description = "If someone has access to the second authentication factor, they only need the account password to log into the account. They could also intercept and delete login notifications."
            )
            risks.append(new_risk)

        elif self.enabled == 'no':
            new_risk = Risk(
                risk = "Two-factor authentication disabled",
                description = "Without two-factor authentication, others only need the account password to log in."
            )
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report


class SecurityQuestions(AccountSection):
    questions = {
        'present': "Does the account use security questions?",
        'know': "Do you believe the person of concern knows the answer to any of these questions?",
        'which': "Which questions might they be able to answer?",
    }
    attrs = AccountSection.attrs + list(questions.keys())
    screenshot_label = "security_questions"

    def generate_risk_report(self):
        '''
        Generate a risk report about security questions. Possible risks:
            - Enabled
            - Known
        '''
        risks = list()

        if self.present == 'yes':

            if self.know == 'yes':
                new_risk = Risk(
                    risk = "Guessable security questions",
                    description = "The client believes the person of concern knows the answers to security questions, which could allow them an easy way to log into the account."

                )
                risks.append(new_risk)

            else:
                new_risk = Risk(
                    risk = "Use of security questions",
                    description = "The account allows login using security questions, which are not secure because they are easy to guess."
                )
                risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report

class InstallInfo(DictInitClass):
    questions = {
        'knew_installed': 'Did you know this app was installed?',
        'installed': 'Did you install this app?',
        'coerced': 'Did the person of concern coerce you into installing this app?'
    }
    attrs = list(questions.keys())

    def generate_risk_report(self, system_app = False):
        risks = list()

        if not system_app:
            if self.knew_installed == 'no' or self.installed == 'no' or self.coerced == 'yes':

                description = ""
                if self.knew_installed == 'no':
                    description = "The client did not know this app was installed, indicating someone else installed it."

                elif self.installed == 'no':
                    description = "The client did not install this app, indicating someone else installed it."

                elif self.coerced == 'yes':
                    description = "The client was coerced into installing this app."

                new_risk = Risk(
                    risk="App installed without permission",
                    description=description
                )
                risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)
        return self.risk_report

class PermissionInfo(DictInitClass):
    questions = {
        "access": "Is any information being leaked to the person of concern through this app?",
        "describe": "If yes, please describe."
    }
    attrs = ['permissions',
             'access',
             'describe']

    def generate_risk_report(self):
        risks = list()

        if self.access == 'yes':
            new_risk = Risk(
                risk="Data leakage",
                description="This app is sharing data with the person of concern."
            )
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)
        return self.risk_report


class AppInfo(Dictable):
    def __init__(self,
                 title="",
                 app_name="",
                 appId="",
                 install_time="",
                 app_version="",
                 last_updated="",
                 flags=None,
                 application_icon="",
                 app_website="",
                 description="",
                 developerwebsite="",
                 investigate=False,
                 permission_info=None,
                 permissions=None,
                 install_info=None,
                 notes=None,
                 device_serial_udid="",
                 **kwargs):

        if flags is None:
            flags = []
        if permission_info is None:
            permission_info = dict()
        if permissions is None:
            permissions = []
        if install_info is None:
            install_info = dict()
        if notes is None:
            notes = dict()
        self.title = title
        self.app_name = app_name
        if self.app_name.strip() == "":
            self.app_name = title
        if self.title.strip() == "":
            self.title = app_name
        if self.app_name.strip() == "" or self.app_name.strip() == "App":
            self.app_name = appId
            self.title = appId
        self.appId = appId

        self.install_time = install_time
        self.app_version = app_version
        self.last_updated = last_updated

        # Fill in flags, removing any flags == ""
        self.flags = list(filter(None, flags))

        self.application_icon = application_icon
        self.app_website = app_website
        self.description = description
        self.developerwebsite = developerwebsite
        self.investigate = investigate

        # I DON"T REALLY KNOW WHY THE BELOW LOGIC IS NECESSARY

        # If permission_info is empty, then we need to create
        # a new PermissionInfo object with the permissions
        if len(permission_info) == 0:
            self.permission_info = PermissionInfo({
                'permissions': permissions
            })

        # Otherwise, create a PermissionInfo object with the provided data
        else:
            self.permission_info = PermissionInfo(permission_info)

        self.install_info = InstallInfo(install_info)
        self.notes = Notes(notes)

        self.device_serial_udid = device_serial_udid
        self.screenshot_files = list()
        self.screenshot_info = list()

    def set_screenshot_files(self, screenshot_files):
        self.screenshot_files = screenshot_files

    def create_screenshot_info(self, get_metadata=True):
        '''
        Creates screenshot objects for all screenshot files related to this app.
        '''
        self.screenshot_info = [ScreenshotInfo(
            fname=fname,
            context="app",
            app_id=self.appId,
            app_name=self.app_name,
            device_serial=self.device_serial_udid,
            get_metadata=get_metadata
        ) for fname in self.screenshot_files]

        return self.screenshot_info

    def _get_flag_risk(self):
        if 'spyware' in self.flags or 'onstore-spyware' in self.flags or 'offstore-spyware' in self.flags:
            return Risk(
                risk="Spyware application",
                description="This app is designed for covert surveillance."
            )
        elif 'regex-spy' in self.flags:
            return Risk(
                risk="Potential spyware application",
                description="This app may be a spyware application based on its title and description."
            )
        return None

    def generate_risk_report(self):
        '''
        Generate a risk report about this app. Possible risks:
            - Flag-based concerns (spyware, offstore)
            - App installed without permission (accounting for system apps)
            - App is sharing data
        '''
        risks = list()

        # Flag-based risk
        flag_risk = self._get_flag_risk()
        if flag_risk:
            risks.append(flag_risk)

        # Data leakage
        data_risks = self.permission_info.generate_risk_report()
        risks.extend(data_risks.risk_details)

        # Installation issues
        install_risks = self.install_info.generate_risk_report(system_app='system-app' in self.flags)
        risks.extend(install_risks.risk_details)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report

class Risk(Dictable):
    def __init__(self,
                 risk="",
                 description=""):
        self.risk = risk
        self.description = description

class RiskReport(Dictable):
    def __init__(self,
                 risk_details=None):
        if risk_details is None:
            risk_details = list()
        self.risk_details = risk_details
        self.risk_present = len(risk_details) > 0

class TAQDevices(DictInitClass):
    questions = {
        'live_together': "Do you live with the person of concern?",
        'purchase_device': "Did the person of concern purchase and/or set up any of your devices?",
        'purchase_device_which': "Which devices did the person of concern purchase and/or set up?",
        'physical_access': "Has the person of concern had physical access to your devices at any point in time?",
        'physical_access_which': "To which devices has the person of concern had physical access?",
        'device_pin': "Can the person of concern unlock any of these devices with PIN, password, or biometrics?",
    }
    attrs = list(questions.keys())

    def generate_risk_report(self) -> RiskReport:
        '''
        Generate a risk report for device compromise. Possible risk:
            - Physical access to devices
        '''
        risks = list()

        # Both indicate the same thing: physical access to devices.
        if self.live_together.lower() == 'yes' or self.physical_access.lower() == 'yes' or self.purchase_device.lower() == 'yes':
            new_risk = Risk(
                risk="Physical access to devices",
                description="A person with physical access to devices might be able to install apps, adjust device configurations, and access or manipulate accounts logged in on that device."
            )
            if self.device_pin.lower() == 'yes':
                new_risk.description += " They can also unlock the device with a PIN, password, or biometrics, which would allow them to access all data on the device."
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report


class TAQAccounts(DictInitClass):
    questions = {'pwd_mgmt': "How do you remember your passwords?",
                 'pwd_mgmt_describe': "Please provide more details on how you remember your passwords.",
                 'pwd_comp': "Do you believe the person of concern knows, or could guess, any of your passwords?",
                 'pwd_comp_which': "Which passwords do you believe are compromised, and why?"}
    attrs = list(questions.keys())

    def generate_risk_report(self) -> RiskReport:
        '''
        Generate a risk report for password compromise. Possible risks:
            - Password compromise
            - Password manager compromise TODO
        '''
        risks = list()

        if self.pwd_comp == 'yes':
            new_risk = Risk(
                risk="Password compromise",
                description="Someone who knows account passwords may be able to access and/or manipulate those accounts."
            )
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report


class TAQSharing(DictInitClass):
    questions = {'share_phone_plan': "Do you share a phone plan with the person of concern?",
                 'phone_plan_admin': "If you share a phone plan, who is the family 'head' or plan administrator?",
                 'share_accounts': "Do you share any accounts with the person of concern?",
                 'share_which': "Which accounts are shared with the person of concern?"}
    attrs = list(questions.keys())

    def generate_risk_report(self) -> RiskReport:
        '''
        Generate a risk report for account compromise due to sharing. Possible risks:
            - Shared phone plan
            - Shared accounts
        '''
        risks = list()

        if self.share_phone_plan == 'yes':
            new_risk = Risk(
                risk="Shared phone plan",
                description="A shared phone plan may leak a variety of information, possibly including call history, message history (but not message content), contacts, and sometimes location. The account administrator of the client's phone plan has even more privileged access to this information."
            )
            # Going to need to reformat the administrator here bc it'll probably say 'poc' not spelled out
            risks.append(new_risk)

        if self.share_accounts == 'yes':
            new_risk = Risk(
                risk="Shared accounts",
                description="The client has shared accounts with the person of concern. Any information on those accounts can be assumed to be known by the person of concern."
            )
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report


class TAQSmarthome(DictInitClass):
    questions = {'smart_home': "Do you have any smart home devices?",
                 'smart_home_setup': "Who installed and set up your smart home devices?",
                 'smart_home_access': "Did the person of concern ever have physical access to the devices?",
                 'smart_home_acct_sharing': "Do you share any smart home accounts with the person of concern?",
                 'smart_home_acct_linking': "Can the person of concern access any of the smart home devices via their own smart home account?"}
    attrs = list(questions.keys())

    def _get_phys_access_risk(self):
        if self.smart_home_setup == 'poc':  # Check that this is what it would be, and not "Person of Concern"
            return Risk(
                risk="Physical access to smart home devices",
                description="With physical access to smart home devices, someone could (1) learn private information, for example by querying a smart speaker, or (2) reconfigure the devices to share information or allow remote control. Someone who initially set up the devices would have even more power to configure as they wish."
            )
        elif self.smart_home_access == 'yes':
            return Risk(
                risk="Physical access to smart home devices",
                description="With physical access to smart home devices, someone could (1) learn private information, for example by querying a smart speaker, or (2) reconfigure the devices to share information or allow remote control."
            )
        return None

    def _get_online_access_risk(self):
        if self.smart_home_acct_sharing == 'yes' or self.smart_home_acct_linking == 'yes':
            return Risk(
                risk="Online access to smart home devices",
                description="Someone with online access to a smart home device might be able to gather data (e.g., viewing video recordings or voice commands used) or manipulate the device state (e.g., turning a light off or locking a smart lock.)"
            )
        return None

    def generate_risk_report(self) -> RiskReport:
        '''
        Generate a risk report for smart home device compromise. Possible risks:
            - Physical access to smart home devices
            - Online access to smart home devices
        '''
        risks = list()

        # Physical access
        phys_access_risk = self._get_phys_access_risk()
        if phys_access_risk:
            risks.append(phys_access_risk)

        # Online access
        online_access_risk = self._get_online_access_risk()
        if online_access_risk:
            risks.append(online_access_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report


class TAQKids(DictInitClass):
    questions = {
        'custody': "If you have children, do they have electronic devices?",
        'child_phys_access': "Has the person of concern had physical access to any of the child(ren)'s devices?",
        'child_phone_plan': "Does the person of concern pay for the child(ren)'s phone plan?"}
    attrs = list(questions.keys())

    def generate_risk_report(self) -> RiskReport:
        '''
        Generate a risk report for children's devices. Possible risks:
            - Physical access to devices
            - Shared phone plan
            - TODO: Other things like accounts shared, location sharing, ??
        '''
        risks = list()

        if self.child_phys_access == 'yes':
            new_risk = Risk(
                risk="Physical access to children's devices",
                description="A person with physical access to children's devices might be able to install apps, adjust device configurations, and access or manipulate accounts logged in on that device. These changes could allow monitoring of the parent, for example by tracking the children's location when they are with their parent."
            )
            risks.append(new_risk)

        if self.child_phone_plan == 'yes':
            new_risk = Risk(
                risk="Shared phone plan (child)",
                description="A shared phone plan may leak a variety of information, possibly including call history, message history (but not message content), contacts, and sometimes location. This could include information about the parent, such as their phone number and location when with the children. The plan administrator has even more privileged access to this information."
            )
            # Going to need to reformat the administrator here bc it'll probably say 'poc' not spelled out
            risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report


class TAQLegal(DictInitClass):
    questions = {
        'legal': "Do you have any ongoing or upcoming legal cases?",
    }
    attrs = list(questions.keys())

class Notes(DictInitClass):
    attrs = ['client_notes', 'consultant_notes']

class RiskFactor():

    def __init__(self, risk, description):
        self.risk = risk
        self.description = description


### REAL CLASSES

class ConsultationData(Dictable):

    def __init__(self,
                 setup = None,
                 taq = None,
                 accounts = None,
                 scans = None,
                 screenshot_dir = "",
                 notes = None,
                 **kwargs):
        # Note: Not used except in printout.
        if setup is None:
            setup = dict()
        if taq is None:
            taq = dict()
        if accounts is None:
            accounts = []
        if scans is None:
            scans = []
        if notes is None:
            notes = dict()
        self.setup = ConsultSetupData(**setup)

        self.taq = TAQData(**taq)
        self.accounts = [AccountInvestigation(**account) for account in accounts]
        self.scans = [ScanData(**scan) for scan in scans]
        self.screenshot_dir = screenshot_dir
        self.notes = ConsultNotesData(**notes)

        # Grab questions that we will use to generate the printout
        # TODO: streamline
        self.formquestions = dict()
        self.formquestions["accounts"] = dict(
            suspicious_logins = SuspiciousLogins().questions,
            password_check = PasswordCheck().questions,
            recovery_settings = RecoverySettings().questions,
            two_factor_settings = TwoFactorSettings().questions,
            security_questions = SecurityQuestions().questions
        )
        self.formquestions["taq"] = dict(
            devices = TAQDevices().questions,
            accounts = TAQAccounts().questions,
            sharing = TAQSharing().questions,
            smarthome = TAQSmarthome().questions,
            kids = TAQKids().questions,
            legal = TAQLegal().questions
        )
        self.formquestions["apps"] = dict(
            permission_info = PermissionInfo().questions,
            install_info = InstallInfo().questions
        )

    def prepare_reports(self):
        '''
        Create all risk reports for the elements of the consultation.
        '''
        self.taq.generate_risk_reports()
        for scan in self.scans:
            scan.generate_risk_report()
        for account in self.accounts:
            account.generate_risk_report()

    def prepare_screenshots(self, get_metadata=True):
        """
        Get all screenshot information for the consultation.
        """

        all_screenshots = get_all_screenshot_files()

        for scan in self.scans:
            if scan.serial_or_udid in list(all_screenshots["devices"].keys()):
                scan_screenshots = all_screenshots["devices"][scan.serial_or_udid]

                scan_root_screenshots = scan_screenshots.get("root", list())
                scan.set_screenshot_files(scan_root_screenshots)
                scan.create_screenshot_info(get_metadata=get_metadata)

                for app in scan.selected_apps:
                    app_screenshots = scan_screenshots.get(app.appId, list())
                    app.set_screenshot_files(app_screenshots)
                    app.create_screenshot_info(get_metadata=get_metadata)

        for account in self.accounts:
            if str(account.account_id) in list(all_screenshots["account_sections"].keys()):
                for section in [account.recovery_settings,
                                account.security_questions,
                                account.suspicious_logins,
                                account.two_factor_settings]:
                    section_screenshots = all_screenshots["account_sections"][str(account.account_id)][section.screenshot_label]
                    section.set_screenshot_files(section_screenshots)
                    section.create_screenshot_info(get_metadata=get_metadata)

class AccountInvestigation(Dictable):
    def __init__(self,
                 account_id=0,
                 platform="",
                 username="",
                 suspicious_logins=None,
                 password_check=None,
                 recovery_settings=None,
                 two_factor_settings=None,
                 security_questions=None,
                 notes=None,
                 **kwargs):
        if suspicious_logins is None:
            suspicious_logins = dict()
        if password_check is None:
            password_check = dict()
        if recovery_settings is None:
            recovery_settings = dict()
        if two_factor_settings is None:
            two_factor_settings = dict()
        if security_questions is None:
            security_questions = dict()
        if notes is None:
            notes = dict()
        self.account_id = account_id
        self.platform = platform
        self.username = username

        # insert account id where needed to get screenshots
        for section in [suspicious_logins, recovery_settings, two_factor_settings, security_questions]:
            section['account_id'] = account_id
        self.suspicious_logins = SuspiciousLogins(suspicious_logins)
        self.password_check = PasswordCheck(password_check)
        self.recovery_settings = RecoverySettings(recovery_settings)
        self.two_factor_settings = TwoFactorSettings(two_factor_settings)
        self.security_questions = SecurityQuestions(security_questions)
        self.notes = Notes(notes)

        self.generate_risk_report()


    def generate_risk_report(self):

        risks = list()

        for obj in [self.suspicious_logins, self.password_check, self.recovery_settings, self.two_factor_settings, self.security_questions]:
            risk_report: RiskReport = obj.generate_risk_report()
            risks.extend(risk_report.risk_details)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report


class ScanData(Dictable):
    def __init__(self,
                 manual=False,
                 scan_id=0,
                 device_type="",
                 device_nickname="",
                 serial="",
                 adb_serial="",
                 serial_or_udid="",  # TODO: Just use this one
                 device_model="",
                 device_version="",
                 device_manufacturer="",
                 is_rooted="",
                 rooted_reasons="",
                 all_apps=None,
                 selected_apps=None,
                 **kwargs):

        if all_apps is None:
            all_apps = list()
        if selected_apps is None:
            selected_apps = list()
        self.manual = manual
        self.scan_id = scan_id
        self.device_type = device_type
        self.device_nickname = device_nickname
        self.serial = serial
        self.serial_or_udid = serial_or_udid
        if self.serial_or_udid.strip() == "":
            self.serial_or_udid = adb_serial
        self.device_model = device_model
        self.device_version = device_version
        self.device_manufacturer = device_manufacturer
        self.is_rooted = is_rooted
        self.rooted_reasons = rooted_reasons

        # sort all_apps by title, with system apps at the end,
        # checked apps at the top, and flagged investigated apps at the top top
        self.all_apps = [AppInfo(**app) for app in all_apps]
        self.all_apps.sort(key=lambda x: x.title.lower())
        self.all_apps.sort(key=lambda x: len(x.flags) > 0, reverse=True)
        self.all_apps.sort(key=lambda x: 'system-app' in x.flags and len(x.flags) == 1)
        self.all_apps.sort(key=lambda x: x.investigate, reverse=True)

        self.selected_apps = [AppInfo(**app) for app in selected_apps]

        self.screenshot_files = list()
        self.screenshot_info = list()

        self.generate_risk_report()

    def set_screenshot_files(self, screenshot_files):
        self.screenshot_files = screenshot_files

    def create_screenshot_info(self, get_metadata=True):
        '''
        Creates screenshot objects for all screenshot files related to this device scan.
        '''
        self.screenshot_info = [ScreenshotInfo(
            fname=fname,
            context="root",
            device_nickname=self.device_nickname,
            device_serial=self.serial,
            get_metadata=get_metadata
        ) for fname in self.screenshot_files]

        return self.screenshot_info

    def generate_risk_report(self):
        '''
        Generate a risk report for this device. Possible risks:
            - Jailbroken device
            - Risk from installed apps (raise up from apps)
        '''
        risks = list()
        self.concerning_apps = list()

        # Jailbreaking
        if self.is_rooted:
            new_risk = Risk(
                risk="Evidence of jailbreaking",
                description="The device may be jailbroken, giving the person of concern nearly unbounded access to the device and the client's activity on the device."
            )
            risks.append(new_risk)

        # Apps
        for a in self.selected_apps:
            app_risk_report = a.generate_risk_report()
            if app_risk_report.risk_present:
                self.concerning_apps.append(a)
                app_risk_list = [r.risk for r in app_risk_report.risk_details]
                new_risk = Risk(
                    risk="Risk from app: {}".format(a.title),
                    description="Risks identified: {}.".format(", ".join(app_risk_list))
                )
                risks.append(new_risk)

        self.risk_report = RiskReport(risk_details=risks)

        return self.risk_report


class TAQData(Dictable):

    def __init__(self,
                 marked_done=False,
                 devices=None,
                 accounts=None,
                 sharing=None,
                 smarthome=None,
                 kids=None,
                 legal=None,
                 **kwargs):
        if devices is None:
            devices = dict()
        if accounts is None:
            accounts = dict()
        if sharing is None:
            sharing = dict()
        if smarthome is None:
            smarthome = dict()
        if kids is None:
            kids = dict()
        if legal is None:
            legal = dict()
        self.marked_done = marked_done
        self.devices = TAQDevices(devices)
        self.accounts = TAQAccounts(accounts)
        #if self.accounts.pwd_comp_which.strip() == "":
        #    self.accounts.pwd_comp_which = "[Not provided]"
        self.sharing = TAQSharing(sharing)
        if self.sharing.phone_plan_admin == []:
            self.sharing.phone_plan_admin = ""
        self.smarthome = TAQSmarthome(smarthome)
        self.kids = TAQKids(kids)
        self.legal = TAQLegal(legal)

        self.generate_risk_reports()

    def generate_risk_reports(self):
        '''
        Generates all of the risk reports for the TAQ subforms.
        Gathers all risks together for the summary.
        '''
        self.all_risks = list()

        for obj in [self.devices, self.accounts, self.sharing, self.smarthome, self.kids]:
            risk_report: RiskReport = obj.generate_risk_report()
            self.all_risks.extend(risk_report.risk_details)

        return self.all_risks


class ConsultSetupData(Dictable):
    def __init__(self,
                 client="",
                 date="",
                 **kwargs):
        self.client = client
        self.date = date

class ConsultNotesData(Dictable):
    def __init__(self,
                 consultant_notes="",
                 client_notes="",
                 **kwargs):
        self.consultant_notes = consultant_notes
        self.client_notes = client_notes

class ScreenshotInfo(Dictable):
    def __init__(self,
                 fname="",
                 context="",  # root, account, or app
                 device_nickname=None,
                 device_serial=None,
                 app_id=None,
                 app_name=None,
                 username=None,
                 account_section=None,
                 get_metadata=True):
        self.fname = fname
        self.context = context

        # For root and app screenshots
        self.device_nickname = device_nickname
        self.device_serial = device_serial

        # Just for app screenshots
        self.app_id = app_id
        self.app_name = app_name

        # Just for account screenshots
        self.username = username
        self.account_section = account_section

        self.metadata = dict()
        if get_metadata:
            self.get_metadata()

    def get_metadata(self):
        """
        Uses exiftool (bash) to get metadata for our PNG screenshots.
        Available metadata:
            - ExifToolVersion
            - FileName
            - Directory
            - FileSize
            - FileModifyDate
            - FileAccessDate
            - FileInodeChangeDate
            - FilePermissions
            - FileType
            - FileTypeExtension
            - MIMEType
            - ImageWidth
            - ImageHeight
            - BitDepth
            - ColorType
            - Compression
            - Filter
            - Interlace
            - SRGBRendering
            - SignificantBits
            - ImageSize
            - Megapixels
        """

        data_to_get = ["FileModifyDate",
                       "FileAccessDate",]

        self.metadata = dict()

        for item in data_to_get:
            result = subprocess.run(
                ["exiftool", "-" + item, self.fname],
                capture_output=True, text=True
            )
            data = result.stdout.split(":", 1)[-1].strip()
            self.metadata[item] = data

        return self.metadata


def get_all_screenshot_files():
    '''
    Gather all screenshot files at once. This will greatly speed up
    compiling screenshot filenames.

    Returns screenshot_files, a dict() with keys:
        - devices: [serial] -> dict():
            - "root" -> list of screenshots
            - [app id] -> list of screenshots
        - account_sections: account id (str) -> dict() with keys:
            - [section label] -> list of screenshots
    '''

    # Everything is in SCREENSHOT_DIR under a device serial number
    # Need to get:
    #   - Device jailbreak (<device ser>/rooting/)
    #   - Device apps (<device ser>/<appid>/)
    #   - Account sections (<any ser>/account<id>_<section>/)

    screenshot_files = dict(
        devices = dict(),  # accessed by ser
        account_sections = dict()  # accessed by account id as a string
    )

    account_pattern = re.compile(r"account\d+_[a-zA-Z_]+")

    overall_screenshot_dir = os.path.join("webstatic", "images", "screenshots")
    if os.path.exists(overall_screenshot_dir):

        # go into all device dirs and subdirs
        device_dirs = [f for f in os.scandir(overall_screenshot_dir) if os.path.isdir(f)]
        for device_dir in device_dirs:
            screenshot_dirs = [f for f in os.scandir(device_dir.path) if os.path.isdir(f)]

            for screenshot_dir in screenshot_dirs:
                # get all screenshot files from this directory
                files = os.listdir(screenshot_dir.path)
                full_fnames = [os.path.join(screenshot_dir, f) for f in files]
                full_fnames.sort()

                if len(full_fnames) > 0:

                    # save the fnames in the right place
                    if screenshot_dir.name == "rooting":
                        if device_dir.name not in list(screenshot_files["devices"].keys()):
                            screenshot_files["devices"][device_dir.name] = dict(
                                root = list()
                            )

                        screenshot_files["devices"][device_dir.name]["root"] = full_fnames

                    elif account_pattern.match(screenshot_dir.name):
                        fname_parts = screenshot_dir.name.split("_", 1)
                        account_id_str = fname_parts[0][-1]
                        account_section = fname_parts[1]

                        if account_id_str not in list(screenshot_files["account_sections"].keys()):
                            section_dict = dict()
                            section_dict[SuspiciousLogins().screenshot_label] = list()
                            section_dict[RecoverySettings().screenshot_label] = list()
                            section_dict[TwoFactorSettings().screenshot_label] = list()
                            section_dict[SecurityQuestions().screenshot_label] = list()
                            screenshot_files["account_sections"][account_id_str] = section_dict

                        screenshot_files["account_sections"][account_id_str][account_section].extend(full_fnames)

                    else:
                        # add if needed
                        if device_dir.name not in list(screenshot_files["devices"].keys()):
                            screenshot_files["devices"][device_dir.name] = dict(
                                root = list()
                            )

                        screenshot_files["devices"][device_dir.name][screenshot_dir.name] = full_fnames

    return screenshot_files
