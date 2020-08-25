tinydb-smartcache
^^^^^^^^^^^^^^^^^

|Build Status| |Coverage| |Version|

``tinydb-smartcache`` provides a smart query cache for TinyDB. It updates the
query cache when inserting/removing/updating elements so the cache doesn't get
invalidated. It's useful if you perform lots of queries while the data changes
only a little.

Installation
************

.. code-block:: bash

    $ pip install tinydb_smartcache

Usage
*****

.. code-block:: python

    >>> from tinydb import TinyDB
    >>> from tinydb_smartcache import SmartCacheTable
    >>> db = TinyDB('db.json')
    >>> db.table_class = SmartCacheTable
    >>> db.table('foo')
    >>> # foo will now use the smart query cache

If you want to enable TinyDB for all databases in a session, run:

.. code-block:: python

    >>> from tinydb import TinyDB
    >>> from tinydb_smartcache import SmartCacheTable
    >>> TinyDB.table_class = SmartCacheTable
    >>> # All databases/tables will now use the smart query cache

Changelog
*********

**v2.0.0** (2020-08-25)
-----------------------

- Add support for TinyDB v4. Drops support for TinyDB <= 3 and Python 2.

**v1.0.3** (2019-10-26)
-----------------------

- Make ``SmartCacheTable`` work again after breakage with TinyDB v3.12.0

**v1.0.2** (2015-11-17)
-----------------------

- Account for changes in TinyDB 3.0

**v1.0.1** (2015-11-17)
-----------------------

- Fix installation via pip

**v1.0.0** (2015-09-17)
-----------------------

- Initial release on PyPI

.. |Build Status| image:: https://img.shields.io/github/workflow/status/msiemens/tinydb-smartcache/Python%20CI?style=flat-square
   :target: https://github.com/msiemens/tinydb-smartcache/actions?query=workflow%3A%22Python+CI%22
.. |Coverage| image:: http://img.shields.io/coveralls/msiemens/tinydb-smartcache.svg?style=flat-square
   :target: https://coveralls.io/r/msiemens/tinydb-smartcache
.. |Version| image:: http://img.shields.io/pypi/v/tinydb-smartcache.svg?style=flat-square
   :target: https://pypi.python.org/pypi/tinydb-smartcache/
