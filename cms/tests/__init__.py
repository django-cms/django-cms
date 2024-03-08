import django


if django.VERSION < (4, 2):  # TODO: remove when dropping support for Django < 4.2
    from django.test.testcases import TransactionTestCase

    TransactionTestCase.assertQuerySetEqual = TransactionTestCase.assertQuerysetEqual