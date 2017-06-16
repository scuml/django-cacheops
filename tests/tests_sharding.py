# -*- coding: utf-8 -*-
from django.test import override_settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connections

from .models import Category, Post
from .tests import BaseTestCase


class PrefixTests(BaseTestCase):
    fixtures = ['basic']

    def test_context(self):
        prefix = ['']
        with override_settings(CACHEOPS_PREFIX=lambda _: prefix[0]):
            with self.assertNumQueries(2):
                Category.objects.cache().count()
                prefix[0] = 'x'
                Category.objects.cache().count()

    @override_settings(CACHEOPS_PREFIX=lambda q: q.db)
    def test_db(self):
        with self.assertNumQueries(1):
            list(Category.objects.cache())

        # HACK: This prevents initialization queries to break .assertNumQueries() in MySQL.
        #       Also there is no .ensure_connection() in older Djangos, thus it's even uglier.
        # TODO: remove in Django 1.10
        connections['slave'].cursor().close()

        with self.assertNumQueries(1, using='slave'):
            list(Category.objects.cache().using('slave'))
            list(Category.objects.cache().using('slave'))

    @override_settings(CACHEOPS_PREFIX=lambda q: q.table)
    def test_table(self):
        self.assertTrue(Category.objects.all()._cache_key().startswith('tests_category'))

        with self.assertRaises(ImproperlyConfigured):
            list(Post.objects.filter(category__title='Django').cache())