from tinydb.database import Table


class SmartCacheTable(Table):
    """
    A Table with a smarter query cache.

    Provides the same methods as :class:`~tinydb.database.Table`.

    The query cache gets updated on insert/update/remove. Useful when in cases
    where many searches are done but data isn't changed often.
    """

    def _write(self, values):
        # Just write data, don't clear the query cache
        self._storage.write(values)

    def insert(self, element):
        # See Table.insert

        # Insert element
        eid = super(SmartCacheTable, self).insert(element)

        # Update query cache
        for query in self._query_cache:
            results = self._query_cache[query]
            if query(element):
                results.append(element)

        return eid

    def insert_multiple(self, elements):
        # See Table.insert_multiple

        # We have to call `SmartCacheTable.insert` here because
        # `Table.insert_multiple` doesn't call `insert()` for every element
        return [self.insert(element) for element in elements]

    def update(self, fields, cond=None, eids=None):
        # See Table.update

        if callable(fields):
            _update = lambda data, eid: fields(data[eid])
        else:
            _update = lambda data, eid: data[eid].update(fields)

        def process(data, eid):
            old_value = data[eid].copy()

            # Update element
            _update(data, eid)
            new_value = data[eid]

            # Update query cache
            for query in self._query_cache:
                results = self._query_cache[query]

                if query(old_value):
                    # Remove old value from cache
                    results.remove(old_value)

                elif query(new_value):
                    # Add new value to cache
                    results.append(new_value)

        self.process_elements(process, cond, eids)

    def remove(self, cond=None, eids=None):
        # See Table.remove

        def process(data, eid):
            # Update query cache
            for query in self._query_cache:

                results = self._query_cache[query]
                try:
                    results.remove(data[eid])
                except ValueError:
                    pass

            # Remove element
            data.pop(eid)

        self.process_elements(process, cond, eids)

    def purge(self):
        # See Table.purge

        super(SmartCacheTable, self).purge()
        self._query_cache.clear()  # Query cache got invalid
