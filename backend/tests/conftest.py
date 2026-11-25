"""
Shared pytest configuration.

API tests run against a real PostgreSQL test database through
tests/pg_support.py (make_engine, make_client, auth) and are skipped when it
is unreachable. There is deliberately no mocked-database client here: the
old MagicMock session let routes run the real services against a fake
database, so tests passed or failed for reasons unrelated to the code.
"""
