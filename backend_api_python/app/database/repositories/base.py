"""Base repository helpers."""


class BaseRepository:
    def __init__(self, session):
        self.session = session

    def add(self, instance):
        self.session.add(instance)
        return instance

    def add_all(self, instances):
        self.session.add_all(instances)
        return instances

    def flush(self):
        self.session.flush()

    def commit(self):
        self.session.commit()

    def refresh(self, instance):
        self.session.refresh(instance)
        return instance
