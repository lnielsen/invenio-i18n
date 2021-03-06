# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Flask-BabelEx domain for merging translations from many directories."""

from __future__ import absolute_import, print_function

import os

from babel.support import NullTranslations, Translations
from flask import _request_ctx_stack
from flask_babelex import Domain, get_locale
from pkg_resources import iter_entry_points, resource_filename, resource_isdir


class NoCompiledTranslationError(Exception):
    """Raised when no compiled *.mo translations are found."""


class MultidirDomain(Domain):
    """Domain supporting merging translations from many catalogs."""

    def __init__(self, paths=[], entrypoint=None, domain='messages'):
        """Initialize domain."""
        self.paths = []
        if entrypoint:
            self.add_entrypoint(entrypoint)
        for p in paths:
            self.add_path(p)
        super(MultidirDomain, self).__init__(domain=domain)

    def has_paths(self):
        """Determine if any paths have been specified."""
        return bool(self.paths)

    def add_entrypoint(self, entrypoint):
        """Load translations from an entrypoint."""
        for ep in iter_entry_points(group=entrypoint):
            if not resource_isdir(ep.module_name, 'translations'):
                continue
            dirname = resource_filename(ep.module_name, 'translations')
            self.add_path(dirname)

    def add_path(self, path):
        """Load translations from a path."""
        if not os.path.exists(path):
            raise RuntimeError("Path does not exists: %s." % path)
        self.paths.append(path)

    def _get_translation_for_locale(self, locale):
        """Get translation for a specific locale."""
        translations = None

        for dirname in reversed(self.paths):
            # Load a single catalog.
            catalog = Translations.load(dirname, [locale], domain=self.domain)
            if translations is None:
                translations = catalog
                continue

            try:
                # Merge catalog into global catalog
                translations.merge(catalog)
            except AttributeError:
                # Translations is probably NullTranslations
                if isinstance(catalog, NullTranslations):
                    raise NoCompiledTranslationError(
                        "Compiled translations seems to be missing in %s."
                        % dirname)
                raise

        return translations or NullTranslations()

    def get_translations(self):
        """Return the correct gettext translations for request.

        This will never fail and return a dummy translation object if used
        outside of the request or if a translation cannot be found.
        """
        ctx = _request_ctx_stack.top
        if ctx is None:
            return NullTranslations()

        locale = get_locale()

        cache = self.get_translations_cache(ctx)

        translations = cache.get(str(locale))

        if translations is None:
            translations = self._get_translation_for_locale(locale)
            cache[str(locale)] = translations

        return translations
