import requests


"""
cbpop BE2269E4
item 252335
cname James Crofts
time 1487674338
cbreceipt 2HE507625W932012F
cemail Shalfeyyy1@yandex.ru
"""

"""
ctransaction SALE
cupsellreceipt
ctransaffiliate 0
ctransvendor 645601
ctranspaymentmethod PYPL
caffitid 22774705
ccustcc
ccustemail Shalfeyyy1@yandex.ru
cprodtitle Testtesttest
ccuststate
cproditem 252335
ctranstime 1487674338
ctransreceipt 2HE507625W932012F
ctransamount 0.50
cvendthru
cprodtype RECURRING
cverify 54E22232
ccustname James Crofts
"""

"""
ctransaction RFND
cupsellreceipt
ctransaffiliate 0
ctransvendor 645601
ctranspaymentmethod PYPL
caffitid 22774705
ccustcc
ccustemail Shalfeyyy1@yandex.ru
cprodtitle Testtesttest
ccuststate
cproditem 252335
ctranstime 1487674338
ctransreceipt 2HE507625W932012F
ctransamount 0.50
cvendthru
cprodtype RECURRING
cverify 319036E0
ccustname James Crofts
"""

"""
ctransaction CANCEL-REBILL
cupsellreceipt
ctransaffiliate 0
ctransvendor 645601
ctranspaymentmethod PYPL
caffitid 22774705
ccustcc
ccustemail Shalfeyyy1@yandex.ru
cprodtitle Testtesttest
ccuststate
cproditem 252335
ctranstime 1487674338
ctransreceipt 2HE507625W932012F
ctransamount 0.50
cvendthru
cprodtype RECURRING
cverify 28F789D2
ccustname James Crofts
"""
"""
ctransaction SALE
cupsellreceipt
ctransaffiliate 0
ctransvendor 645601
ctranspaymentmethod PYPL
caffitid 22812471
ccustcc
ccustemail Shalfeyyy1@yandex.ru
cprodtitle Testtesttest
ccuststate
cproditem 252335
ctranstime 1487879263
ctransreceipt 9FM37031T5943151T
ctransamount 0.50
cvendthru
cprodtype RECURRING
cverify 19FD4F69
ccustname James Crofts
[23/Feb/2017 14:47:57]"POST /jvzipn/ HTTP/1.1" 200 0
cbpop E0E88BD4
item 252335
cname James Crofts
time 1487879263
cbreceipt 9FM37031T5943151T
cemail Shalfeyyy1@yandex.ru
"""
url = 'https://5c83ef36.ngrok.io/'
params = {
    u'ctransaction': u'SALE', u'cupsellreceipt': u'',
    u'ctransaffiliate': u'0', u'ctransvendor': u'645601',
    u'ctranspaymentmethod': u'PYPL', u'caffitid': u'22812471',
    u'ccustcc': u'', u'ccustemail': u'Shalfeyyy1@yandex.ru',
    u'cprodtitle': u'Testtesttest', u'ccuststate': u'',
    u'cproditem': u'252335', u'ctranstime': u'1487879263',
    u'ctransreceipt': u'9FM37031T5943151T', u'ctransamount': u'0.50',
    u'cvendthru': u'', u'cprodtype': u'RECURRING',
    u'cverify': u'19FD4F69', u'ccustname': u'James Crofts',
}
params2 = {
    u'cbpop': u'BE2269E4',
u'item': u'252335',
u'cname': u'James Crofts',
u'time': u'1487674338',
u'cbreceipt': u'2HE507625W932012F',
u'cemail': u'Shalfeyyy1@yandex.ru'
}
# resp = requests.get(url + 'payment_success/', params=params2)
resp = requests.post(url + 'jvzipn/', data=params)
print resp.status_code