import string
import unittest

import support  # noqa: F401
from osat_manager_git.messages import (LANGUAGES, Messages, choose_language,
                                       load_catalogue)


def fields(template):
    return {name for _, name, _, _ in string.Formatter().parse(template)
            if name}


class CatalogueTests(unittest.TestCase):
    def test_same_keys_and_placeholders(self):
        source = load_catalogue("en-ca")
        for language in LANGUAGES:
            catalogue = load_catalogue(language)
            self.assertEqual(set(catalogue), set(source), language)
            for key, template in catalogue.items():
                self.assertTrue(template.strip(), f"{language}:{key}")
                self.assertEqual(fields(template), fields(source[key]),
                                 f"{language}:{key}")

    def test_render(self):
        say = Messages("fr-ca")
        self.assertIn("2.40.0", say("problem_version_too_old",
                                    found="2.40.0", minimum="2.49.0"))

    def test_unknown_key_shown_as_is(self):
        self.assertEqual(Messages()("line 3: tabs are not allowed"),
                         "line 3: tabs are not allowed")


class LanguageTests(unittest.TestCase):
    def test_choice(self):
        self.assertEqual(choose_language("fr-ca", {}), "fr-ca")
        self.assertEqual(choose_language(None, {"LANG": "fr_CA.UTF-8"}),
                         "fr-ca")
        self.assertEqual(choose_language(None, {"LANG": "fr_FR.UTF-8"}),
                         "fr-ca")
        self.assertEqual(choose_language(None, {"OSAT_LANG": "en-ca",
                                                "LANG": "fr_CA.UTF-8"}),
                         "en-ca")
        self.assertEqual(choose_language(None, {"LANG": "de_DE.UTF-8"}),
                         "en-ca")
        self.assertEqual(choose_language(None, {}), "en-ca")


if __name__ == "__main__":
    unittest.main()
