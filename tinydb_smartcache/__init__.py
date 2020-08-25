from tinydb.table import Table, Document
from tinydb.storages import Storage
from tinydb.queries import Query

from typing import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Union,
    cast
)


class SmartCacheTable(Table):
    """
    A Table with a smarter query cache.

    Provides the same methods as :class:`~tinydb.database.Table`.

    The query cache gets updated on insert/update/remove. Useful when in cases
    where many searches are done but data isn't changed often.
    """

    def __init__(
            self,
            storage: Storage,
            name: str,
            cache_size: int = Table.default_query_cache_capacity
    ):

        super().__init__(storage, name, cache_size)

    def insert(self, document: Mapping) -> int:
        # Insert document
        doc_id = super().insert(document)

        # Update Query Cache
        for query in self._query_cache.lru:
            results = self._query_cache[query]
            if query(document) and results is not None:
                results.append(document)

        return doc_id

    def insert_multiple(self, documents: Iterable[Mapping]) -> List[int]:
        # Insert documents
        doc_ids = super().insert_multiple(documents)

        # Update Query Cache
        for query in self._query_cache.lru:
            results = self._query_cache[query]
            if results is not None:
                for doc in documents:
                    if query(doc):
                        results.append(doc)

        return doc_ids

    def search(self, cond: Query) -> List[Document]:
        # First, we check the query cache to see if it has results for this
        # query
        if cond in self._query_cache:
            docs = self._query_cache.get(cond)
            if docs is not None:
                return docs[:]

        # Perform the search by applying the query to all documents
        docs = [doc for doc in self if cond(doc)]

        # Update the query cache
        self._query_cache[cond] = docs[:]

        return docs

    def get(
            self,
            cond: Optional[Query] = None,
            doc_id: Optional[int] = None,
    ) -> Optional[Document]:

        # Check Query Cache
        if (doc_id is None) and (cond is not None):
            if cond in self._query_cache:
                for doc in self._query_cache.get(cond):
                    if cond(doc):
                        return doc

        return super().get(cond, doc_id)

    def update(
            self,
            fields: Union[Mapping, Callable[[Mapping], None]],
            cond: Optional[Query] = None,
            doc_ids: Optional[Iterable[int]] = None,
    ) -> List[int]:

        if callable(fields):
            def perform_update(doc):
                # Update documents by calling the update function provided by
                # the user
                fields(doc)
        else:
            def perform_update(doc):
                # Update documents by setting all fields from the provided data
                doc.update(fields)

        def perform_update_override(doc):
            old_value = doc.copy()

            # Update element
            perform_update(doc)
            new_value = doc

            # Update Query Cache
            for query in self._query_cache.lru:
                results = self._query_cache[query]

                if query(old_value):
                    # Remove old value from cache
                    results.remove(old_value)

                if query(new_value):
                    # Add new value to cache
                    results.append(new_value)

        return super().update(perform_update_override, cond, doc_ids)

    def remove(
            self,
            cond: Optional[Query] = None,
            doc_ids: Optional[Iterable[int]] = None,
    ) -> List[int]:

        if cond is None and doc_ids is None:
            raise RuntimeError('Use truncate() to remove all documents')

        # Remove From Query Cache
        if doc_ids is not None:
            docs_by_id = [self.get(doc_id=x) for x in doc_ids]
        for query in self._query_cache.lru:
            if (not cond is None) and (query == cond):
                del self._query_cache[query]
            else:
                for doc in self._query_cache[query]:
                    if ((cond is not None) and cond(doc))\
                            or ((doc_ids is not None) and doc in docs_by_id):
                        self._query_cache[query].remove(doc)

        return super().remove(cond, doc_ids)

    def truncate(self) -> None:
        super().truncate()

        self.clear_cache()

    def _update_table(self, updater: Callable[[Dict[int, Mapping]], None]):
        """
        Perform an table update operation.
        The storage interface used by TinyDB only allows to read/write the
        complete database data, but not modifying only portions of it. Thus
        to only update portions of the table data, we first perform a read
        operation, perform the update on the table data and then write
        the updated data back to the storage.
        As a further optimization, we don't convert the documents into the
        document class, as the table data will *not* be returned to the user.
        """

        tables = self._storage.read()

        if tables is None:
            # The database is empty
            tables = {}

        try:
            raw_table = tables[self.name]
        except KeyError:
            # The table does not exist yet, so it is empty
            raw_table = {}

        # Convert the document IDs to the document ID class.
        # This is required as the rest of TinyDB expects the document IDs
        # to be an instance of ``self.document_id_class`` but the storage
        # might convert dict keys to strings.
        table = {
            self.document_id_class(doc_id): doc
            for doc_id, doc in raw_table.items()
        }

        # Perform the table update operation
        updater(table)

        # Convert the document IDs back to strings.
        # This is required as some storages (most notably the JSON file format)
        # don't require IDs other than strings.
        tables[self.name] = {
            str(doc_id): doc
            for doc_id, doc in table.items()
        }

        # Write the newly updated data back to the storage
        self._storage.write(tables)
