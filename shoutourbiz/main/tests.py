from django.test import TestCase
import models

class TestIPN(TestCase):

    def setUp(self):
        self.user = models.AuthUser.objects.create_user('testuser@gmail.com', '12345q')
        self.ipn_data = {
            u'ctransaction': u'SALE', u'cupsellreceipt': u'',
            u'ctransaffiliate': u'0', u'ctransvendor': u'645601',
            u'ctranspaymentmethod': u'PYPL', u'caffitid': u'22774705',
            u'ccustcc': u'', u'ccustemail': u'Shalfeyyy1@yandex.ru',
            u'cprodtitle': u'Testtesttest', u'ccuststate': u'',
            u'cproditem': u'252335', u'ctranstime': u'1487674338',
            u'ctransreceipt': u'2HE507625W932012F', u'ctransamount': u'0.50',
            u'cvendthru': u'', u'cprodtype': u'RECURRING',
            u'cverify': u'54E22232', u'ccustname': u'James Crofts',
        }

        self.thanks_page_data = {
            u'cbpop': u'BE2269E4',
            u'item': u'252335',
            u'cname': u'James Crofts',
            u'time': u'1487674338',
            u'cbreceipt': u'2HE507625W932012F',
            u'cemail': u'Shalfeyyy1@yandex.ru'
        }

    def test_first_payment_successful(self):
        resp = self.client.post('main:jvzipn')
        self.assertEqual(resp.status_code, 200)