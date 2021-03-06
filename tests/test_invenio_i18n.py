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

"""Basic tests."""

from __future__ import absolute_import, print_function

from datetime import datetime

from flask import render_template_string
from flask_babelex import format_datetime, format_number, get_locale, \
    gettext, lazy_gettext
from pytz import timezone

from invenio_i18n import InvenioI18N


def test_version():
    """Test version import."""
    from invenio_i18n import __version__
    assert __version__


def test_init(app):
    """Test extension initalization."""
    i18n = InvenioI18N(app)
    assert i18n.babel
    assert i18n.entrypoint
    assert app.config.get("I18N_LANGUAGES") == []
    assert 'toutc' in app.jinja_env.filters
    assert 'tousertimezone' in app.jinja_env.filters


def test_init_ext(app):
    """Test extension initalization."""
    app.config["I18N_LANGUAGES"] = ["da"]
    i18n = InvenioI18N(entrypoint=None)
    i18n.init_app(app)
    assert i18n.babel


def test_default_lang(app):
    """Test default language."""
    app.config.update(I18N_LANGUAGES=["en", "de"], BABEL_DEFAULT_LOCALE="da")
    i18n = InvenioI18N(app)
    with app.app_context():
        assert [str(x) for x in i18n.get_locales()] == ['da', 'en', 'de']


def test_json_encoder(app):
    """Test extension initalization."""
    InvenioI18N(app)
    assert app.json_encoder().encode("test") == '"test"'
    assert app.json_encoder().encode(lazy_gettext("test")) == '"test"'


def test_timezone_selector(app):
    """Test format_datetime."""
    app.config['I18N_LANGUAGES'] = ['da']
    InvenioI18N(app)
    with app.test_request_context():
        assert format_datetime(datetime(1987, 3, 5, 17, 12)) == \
            'Mar 5, 1987, 5:12:00 PM'
        assert format_datetime(datetime(1987, 3, 5, 17, 12), 'full') == \
            'Thursday, March 5, 1987 at 5:12:00 PM GMT+00:00'
        assert format_datetime(datetime(1987, 3, 5, 17, 12), 'short') == \
            '3/5/87, 5:12 PM'
        assert format_datetime(datetime(1987, 3, 5, 17, 12), 'dd mm yyy') == \
            '05 12 1987'
        assert format_datetime(datetime(1987, 3, 5, 17, 12), 'dd mm yyyy') \
            == '05 12 1987'
    with app.test_request_context(headers=[('Accept-Language', 'da')]):
        assert str(get_locale()) == 'da'
        assert format_datetime(datetime(1987, 3, 5, 17, 12)) == \
            '05/03/1987 17.12.00'


def test_locale_selector(app):
    """Test locale selector."""
    app.config['I18N_LANGUAGES'] = ['da']
    InvenioI18N(app)

    with app.test_request_context(headers=[('Accept-Language', 'da')]):
        assert str(get_locale()) == 'da'
        assert format_number(10.1) == '10,1'
        assert gettext('Translate') == u'Oversætte'
    with app.test_request_context(headers=[('Accept-Language', 'en')]):
        assert str(get_locale()) == 'en'
        assert format_number(10.1) == '10.1'
        assert gettext('Translate') == 'Translate'


def test_get_locales(app):
    """Test getting locales."""
    app.config['I18N_LANGUAGES'] = ['da']
    i18n = InvenioI18N(app)

    with app.app_context():
        assert [str(l) for l in i18n.get_locales()] == ['en', 'da']


def test_jinja_templates(app):
    """Test template rendering."""
    InvenioI18N(app)

    assert app.jinja_env.filters['datetimeformat']
    assert app.jinja_env.filters['toutc']
    assert app.jinja_env.filters['tousertimezone']

    dt = datetime(1987, 3, 5, 17, 12)
    dt_tz = datetime(1987, 3, 5, 17, 12, tzinfo=timezone('CET'))

    with app.test_request_context():
        assert render_template_string(
            "{{dt|datetimeformat}}", dt=dt) == \
            "Mar 5, 1987, 5:12:00 PM"
        assert render_template_string(
            "{{dt|toutc}}", dt=dt_tz) == \
            "1987-03-05 16:12:00"
        assert render_template_string(
            "{{dt|tousertimezone}}", dt=dt_tz) == \
            "1987-03-05 16:12:00+00:00"
        assert render_template_string("{{_('Translate')}}") == 'Translate'

        tpl = r"{% trans %}Block translate{{var}}{% endtrans %}"
        assert render_template_string(tpl, var='!') == 'Block translate!'
