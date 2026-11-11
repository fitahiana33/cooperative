"""Safety helpers for destructive PostgreSQL test setup."""

from contextlib import contextmanager
import re
from uuid import uuid4

from sqlalchemy.engine import make_url


_SCHEMA_PATTERN = re.compile(r"qa_[a-z0-9_]{1,55}")


def schema_test_url(database_url: str, schema: str) -> str:
    """Route a connection to an isolated schema in the application database."""
    if not _SCHEMA_PATTERN.fullmatch(schema):
        raise RuntimeError(
            "Le schema de verification doit commencer par qa_ et contenir "
            "uniquement des lettres minuscules, chiffres et underscores."
        )
    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or url.query:
        raise RuntimeError(
            "La connexion doit designer explicitement PostgreSQL, sans options de redirection."
        )
    return url.update_query_dict(
        {"options": f"-csearch_path={schema}"}
    ).render_as_string(hide_password=False)


def test_schema_from_url(database_url: str) -> str:
    """Return the controlled QA schema encoded in a test connection URL."""
    options = make_url(database_url).query.get("options", "")
    match = re.fullmatch(r"-csearch_path=(qa_[a-z0-9_]{1,55})", options)
    if not match:
        raise RuntimeError("L'URL ne designe pas un schema QA isole.")
    return match.group(1)


@contextmanager
def temporary_test_schema(database_url: str, schema: str | None = None):
    """Create and later remove only a uniquely owned QA schema."""
    import psycopg
    from psycopg import sql

    url = make_url(database_url).set(query={})
    schema = schema or "qa_migration_" + uuid4().hex[:16]
    if not _SCHEMA_PATTERN.fullmatch(schema):
        raise RuntimeError("Nom de schema QA invalide.")
    ownership = "cooperative-qa-owned:" + uuid4().hex
    target = schema_test_url(url.render_as_string(hide_password=False), schema)
    connection_url = url.set(drivername="postgresql").render_as_string(
        hide_password=False
    )

    with psycopg.connect(connection_url, autocommit=True) as connection:
        exists = connection.execute(
            "SELECT to_regnamespace(%s)", (schema,)
        ).fetchone()[0]
        if exists is not None:
            raise RuntimeError(
                "Schema deja present : aucune modification ni suppression autorisee."
            )
        connection.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        connection.execute(
            sql.SQL("COMMENT ON SCHEMA {} IS {}").format(
                sql.Identifier(schema), sql.Literal(ownership)
            )
        )

    try:
        yield target
    finally:
        with psycopg.connect(connection_url, autocommit=True) as connection:
            actual = connection.execute(
                "SELECT obj_description(oid, 'pg_namespace') "
                "FROM pg_namespace WHERE nspname=%s",
                (schema,),
            ).fetchone()
            if actual != (ownership,):
                raise RuntimeError(
                    "Propriete du schema non confirmee : nettoyage refuse."
                )
            connection.execute(
                sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema))
            )


def validate_test_database_urls(
    target: str, application: str = ""
) -> tuple[str, str]:
    """Validate the legacy dedicated-test-database mode before recreation."""
    url = make_url(target)
    name = url.database or ""
    if {"host", "port", "dbname", "service"}.intersection(url.query):
        raise RuntimeError(
            "La cible des tests doit etre definie dans l'URL, sans redirection."
        )
    if url.get_backend_name() != "postgresql" or not name.endswith("_test"):
        raise RuntimeError(
            "La base des tests doit etre PostgreSQL et son nom doit finir par _test."
        )
    if application:
        source = make_url(application)

        def normalized_host(value):
            return "loopback" if value in {"localhost", "127.0.0.1", "::1"} else value

        if (normalized_host(url.host), url.port or 5432, name) == (
            normalized_host(source.host),
            source.port or 5432,
            source.database,
        ):
            raise RuntimeError(
                "La base des tests doit etre differente de la base applicative."
            )
    admin_url = url.set(drivername="postgresql", database="postgres")
    return admin_url.render_as_string(hide_password=False), name
