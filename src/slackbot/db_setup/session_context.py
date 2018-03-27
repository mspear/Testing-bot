from .make_db_session import make_session


class DBSession:

    def __init__(self, commit=True):
        self.commit = commit

        self.session = None

    def __enter__(self):
        self.session = make_session()

        return self.session


    def __exit__(self, exc_type, exc_val, exc_tb):
        if (self.commit and (not exc_type)):
            self.session.commit()

        self.session.close()
