"""Every message manage-git shows, from a catalogue per language.

Catalogues are JSON files in ``messages/``, one per language tag, each
mapping a message key to text with ``{placeholders}``. en-ca is the source
language; every other catalogue holds exactly the same keys and the same
placeholders, which the unit tests enforce (requirement GIT-7).

The YAML subset reader copied from osat-manager-restic raises English
text rather than catalogue keys. That text is shown as it is, and is part
of the known debt decision 0001 lists.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Mapping, Optional

SOURCE_LANGUAGE = "en-ca"
LANGUAGES = ("en-ca", "fr-ca")
CATALOGUE_DIR = Path(__file__).resolve().parent / "messages"


def load_catalogue(language: str) -> Dict[str, str]:
    path = CATALOGUE_DIR / f"{language}.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def choose_language(requested: Optional[str] = None,
                    environ: Mapping[str, str] = os.environ) -> str:
    """The language to speak: ``--lang``, then OSAT_LANG, then the locale
    variables, falling back to the source language."""
    candidates = [requested, environ.get("OSAT_LANG"), environ.get("LC_ALL"),
                  environ.get("LC_MESSAGES"), environ.get("LANG")]
    for candidate in candidates:
        if not candidate:
            continue
        tag = candidate.split(".")[0].replace("_", "-").lower()
        if tag in LANGUAGES:
            return tag
        if tag.split("-")[0] == "fr":
            return "fr-ca"
        if tag.split("-")[0] == "en":
            return "en-ca"
    return SOURCE_LANGUAGE


class Messages:
    def __init__(self, language: str = SOURCE_LANGUAGE):
        self.language = language
        self.catalogue = load_catalogue(language)
        self.source = (self.catalogue if language == SOURCE_LANGUAGE
                       else load_catalogue(SOURCE_LANGUAGE))

    def __call__(self, key: str, /, **fields: object) -> str:
        template = self.catalogue.get(key) or self.source.get(key)
        if template is None:
            return key
        return template.format(**fields)
