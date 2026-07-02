import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.database import get_db


class MockCollection:
    def __init__(self):
        self.docs = {}

    async def find_one(self, filter):
        for doc in self.docs.values():
            match = True
            for k, v in filter.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                return doc.copy()
        return None

    async def insert_one(self, doc):
        from bson import ObjectId
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.docs[doc["_id"]] = doc
        
        class Result:
            inserted_id = doc["_id"]
        return Result()

    async def update_one(self, filter, update):
        from bson import ObjectId
        # Simplify filter lookup for objectId
        doc = None
        if "_id" in filter:
            doc = self.docs.get(filter["_id"])
        else:
            doc = await self.find_one(filter)
            
        if doc:
            if "$set" in update:
                for k, v in update["$set"].items():
                    doc[k] = v
            self.docs[doc["_id"]] = doc
            
        class Result:
            modified_count = 1 if doc else 0
        return Result()

    async def count_documents(self, filter):
        return len(self.docs)

    def find(self, filter):
        class Cursor:
            def __init__(self, docs):
                self.docs = list(docs)
                self.index = 0
                
            def skip(self, n):
                self.docs = self.docs[n:]
                return self
                
            def limit(self, n):
                self.docs = self.docs[:n]
                return self
                
            def __aiter__(self):
                return self
                
            async def __anext__(self):
                if self.index < len(self.docs):
                    val = self.docs[self.index].copy()
                    self.index += 1
                    return val
                raise StopAsyncIteration
                
        return Cursor(self.docs.values())


class MockDB:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection()
        return self.collections[name]


@pytest.fixture(scope="function")
def db():
    return MockDB()


@pytest.fixture(scope="function")
def client(db):
    async def override_get_db():
        yield db
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
