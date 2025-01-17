SEPA XML Generator
==================

.. image:: https://travis-ci.org/raphaelm/python-sepaxml.svg?branch=master
   :target: https://travis-ci.org/raphaelm/python-sepaxml

.. image:: https://codecov.io/gh/raphaelm/python-sepaxml/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/raphaelm/python-sepaxml

.. image:: http://img.shields.io/pypi/v/sepaxml.svg
   :target: https://pypi.python.org/pypi/sepaxml

This is a python implementation to generate SEPA XML files.

Limitations
-----------

Supported standards:

* CBIPaymentRequest.00.04.00
* SEPA PAIN.001.001.03
* SEPA PAIN.008.001.02
* SEPA PAIN.008.002.02
* SEPA PAIN.008.003.02


Usage
-----


Credit transfer
"""""""""""""""

Example:

.. code:: python

    from sepaxml import SepaTransfer
    import datetime, uuid
    import os

    config = {
    "name"             :        "Test von Testenstein",
    "IBAN"             :        "NL50BANK1234567890",
    "BIC"              :        "BANKNL2A",
    "batch"            :         True,
    "execution_date"   :         datetime.date.today(),
    "priority"         :         False,
    "notify"           :         False,
    "bank_code"        :        "abcwwoe",
    "issuer_id"        :        '123aaf',                                     # For non-SEPA transfers, set "domestic" to True, necessary e.g. for CH/LI
    "currency"         :        "EUR"                                         # ISO 4217
    }
    sepa = SepaTransfer(config, clean=True)

    payment1 = {
        "name": "Test von Testenstein",
        "IBAN": "NL50BANK987654321",
        "BIC": "BANKNL2A",
        "amount": 5000,  # in cents
        "execution_date": datetime.date.today(),
        "description": "Test transaction",
        "endtoend_id": str(uuid.uuid4().hex)  # optional
    }
    sepa.add_payment(payment1)
    
    payment2 = {
        "name": "Test von Testenstein",
        "IBAN": "NL50BANK987654321",
        "BIC": "BANKNL2A",
        "amount": 5000,  # in cents
        "execution_date": datetime.date.today(),
        "document": [{"type":"CINV", "number":"1", "date":datetime.date.today(), "amount":"5000", "description":"hi, hello"}, {"type":"CINV", "number":"2", "date":datetime.date.today(), "amount":"7000", "description":"hello, hi"}],
        "endtoend_id": str(uuid.uuid4().hex)  # optional
    }
    sepa.add_payment(payment2)
    
    
    output = sepa.export(validate=True).decode('utf-8')
    print(output)
    
    path = os.path.expanduser('~\Desktop\output.xml')    
    with open(path, "w") as f:
        f.write(output)



Development
-----------

To automatically sort your Imports as required by CI::

    pip install isort
    isort -rc .


Credits and License
-------------------

Maintainer: Raphael Michel <mail@raphaelmichel.de>

This basically started as a properly packaged, python 3 tested version
of the `PySepaDD`_ implementation that was released by The Congressus under the MIT license.
Thanks for your work!

License: MIT

.. _PySepaDD: https://github.com/congressus/PySepaDD
