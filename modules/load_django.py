import os
import sys
import django

sys.path.append("D:/company-sipius/braincom_playwright_project")
os.environ["DJANGO_SETTINGS_MODULE"] = "braincom_project.settings"
django.setup()
