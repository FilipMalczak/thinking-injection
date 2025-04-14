from terminusdb_client.errors import DatabaseError


def not_found_as_None(foo, *args, **kwargs):
    try:
        return foo(*args, **kwargs)
    except DatabaseError as e:
        if e.status_code == 404:
            return None
        raise