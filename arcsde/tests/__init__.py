import os
import sys
import django

if django.VERSION < (3, 2):
    default_app_config = 'arcsde.tests.apps.ArcSdeTestsConfig'

TEST_SETTINGS = "arcsde.tests.settings"

def setup_django_settings():
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.getcwd())
    os.environ["DJANGO_SETTINGS_MODULE"] = TEST_SETTINGS


def run_tests():
    if not os.environ.get("DJANGO_SETTINGS_MODULE", False):
        setup_django_settings()

    import django
    from django.conf import settings
    from django.test.utils import get_runner

    django.setup()
    runner = get_runner(settings,"django.test.runner.DiscoverRunner")
    test_suite = runner(verbosity=2, interactive=True, failfast=False)
    return test_suite.run_tests(["arcsde"])
