from bd_initialization.DataBase_models import session_local

def get_session():
    """
    Dependency function to provide a database session.
    Yields the session to the caller and ensures it is closed 
    after the request is processed, regardless of success or failure.
    """
    bd = session_local()
    try:
        yield bd
    finally:
        # Close the database session to release resources
        bd.close()