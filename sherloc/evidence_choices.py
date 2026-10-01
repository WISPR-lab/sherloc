"""Choice lists and defaults shared by the consultation forms and data model."""
import os

TMP_CONSULT_DATA_DIR = "tmp-consult-data"

SCREENSHOT_FOLDER = os.path.join("tmp", "isdi-screenshots/")
CONTEXT_PKL_FNAME = "context.pkl"

YES_NO_DEFAULT = ""
PERSON_DEFAULT = ""
LEGAL_DEFAULT = ""
TWO_FACTOR_DEFAULT = ""

SECOND_FACTORS = ["Phone", "Email", "Authenticator App", "Trusted Device", "Other"]
ACCOUNTS = ["Google", "iCloud", "Microsoft", "Lyft", "Uber", "Doordash", "Grubhub", "Facebook", "Twitter", "Snapchat", "Instagram"]

EMPTY_CHOICE = [('', 'Nothing selected')]
YES_NO_UNSURE_CHOICES = EMPTY_CHOICE + [('yes', 'Yes'), ('no', 'No'), ('unsure', 'Unsure')]
YES_NO_CHOICES = EMPTY_CHOICE + [('yes', 'Yes'), ('no', 'No')]
PERSON_CHOICES = [('me', 'Me'), ('poc', 'Person of concern'), ('someoneelse', 'Someone else'), ('unsure', 'Unsure')]
PWD_CHOICES = [('online', 'Online notes'), ('paper', 'Paper notes'), ('pwd_manager', 'Password manager'), ('photo', "Take a photo of it"), ('other_pwd', 'Other'), ('none', 'No specific method')]

LEGAL_CHOICES = [('ro', 'Restraining order'), ('div', 'Divorce or other family court'), ('cl', 'Criminal case'), ('other_legal', 'Other')]
DEVICE_TYPE_CHOICES = EMPTY_CHOICE + [('android', 'Android'), ('ios', 'iOS')]
#two_factor_choices = [empty_choice] + [(x.lower(), x) for x in second_factors]
TWO_FACTOR_CHOICES = [(x.lower().replace(" ", "_"), x) for x in SECOND_FACTORS]
ACCOUNT_CHOICES = [(x, x) for x in ACCOUNTS]
