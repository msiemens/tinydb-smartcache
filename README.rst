tinydb-smartcache
^^^^^^^^^^^^^^^^^

|Build Status| |Coverage| |Version|

``tinydb-smartcache`` provides a smart query cache for TinyDB. It updates the
query cache when inserting/removing/updating elements so the cache doesn't get
invalidated. It's useful if you perform lots of queries while the data changes
only little.

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

**v1.0.1** (2015-11-17)
-----------------------

- Fix installation via pip

**v1.0.0** (2015-09-17)
-----------------------

- Initial release on PyPI

.. |Build Status| image:: http://img.shields.io/travis/msiemens/tinydb-smartcache.svg?style=flat-square
   :target: https://travis-ci.org/msiemens/tinydb-smartcache
.. |Coverage| image:: http://img.shields.io/coveralls/msiemens/tinydb-smartcache.svg?style=flat-square
   :target: https://coveralls.io/r/msiemens/tinydb-smartcache
.. |Version| image:: http://img.shields.io/pypi/v/tinydb-smartcache.svg?style=flat-square
   :target: https://pypi.python.org/pypi/tinydb-smartcache/
