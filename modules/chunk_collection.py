import uuid
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
    SearchResult,
)
from .logger import logger
from .embeddings import text_to_embeddings

connections.connect(alias="default", host="127.0.0.1", port="19530")


class ChunkCollection:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.init()

    def init(self):
        if utility.has_collection(self.collection_name):
            logger.info(f"Collection '{self.collection_name}' already exists.")
            self.collection = Collection(self.collection_name)
            self.load()
            return

        fields = [
            FieldSchema(
                name="chunk_uuid",
                dtype=DataType.VARCHAR,
                max_length=64,
                is_primary=True,
                description="Unique identifier for the chunk",
            ),
            FieldSchema(
                name="page_uuid",
                dtype=DataType.VARCHAR,
                max_length=64,
                description="Identifier of the associated page",
            ),
            FieldSchema(
                name="index",
                dtype=DataType.INT64,
                description="Character index in the page text",
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=65535,
                description="Text content of the chunk",
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=384,
                description="Embedding vector of the chunk",
            ),
        ]

        schema = CollectionSchema(fields, description="Schema for storing text chunks")
        self.collection = Collection(name=self.collection_name, schema=schema)
        logger.info(f"Collection '{self.collection_name}' created successfully.")

        self.load()

    def load(self):
        if not self.collection.indexes:
            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "L2",
                "params": {"nlist": 128},
            }
            self.collection.create_index(field_name="vector", index_params=index_params)
            logger.info("Index created on 'vector' field.")
        else:
            logger.info("Index already exists on 'vector' field.")
        self.collection.load()
        logger.info(f"Collection '{self.collection_name}' loaded successfully.")

    def write_content(self, page_uuid: str, content: str):
        """
        Insert text chunks into the specified Milvus collection.

        Args:
            page_uuid (str): Unique identifier for the page.
            content (str): The text to be chunked and inserted.
        """
        chunk_uuids = []
        page_uuids = []
        char_indices = []
        contents = []
        embeddings = []

        for index, chunk_text, token_count, embedding in text_to_embeddings(content):
            chunk_uuids.append(str(uuid.uuid4()))
            page_uuids.append(page_uuid)
            char_indices.append(index)
            contents.append(chunk_text)
            embeddings.append(embedding)

        entities = [chunk_uuids, page_uuids, char_indices, contents, embeddings]
        self.collection.insert(entities)
        logger.info(
            f"Inserted {len(chunk_uuids)} chunks into collection '{self.collection_name}'."
        )

    def retrieve_chunks(self, limit: int = 1000):
        """
        Retrieve records from the specified Milvus collection with a limit.

        Args:
            limit (int): Maximum number of records to retrieve (default: 1000).

        Returns:
            list[dict]: List of retrieved records as dictionaries.
        """
        results = self.collection.query(
            expr="",
            limit=limit,
            output_fields=[field.name for field in self.collection.schema.fields],
        )

        for index, record in enumerate(results, 1):
            logger.info(f"Record {index}:")
            for key, value in record.items():
                if key == "vector":
                    logger.info(f"  {key}: {value[:10]} ...")
                else:
                    logger.info(f"  {key}: {value}")
            logger.info("---")

        return results

    def search_top_k_chunks(self, top_k: int, query_text: str):
        """
        Search for top K similar chunks based on the query text.

        Args:
            top_k (int): Number of top similar results to retrieve.
            query_text (str): The input question or text.

        Returns:
            list[dict]: Top K matched chunks.
        """
        query_embeddings = [i[3] for i in list(text_to_embeddings(query_text))]

        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

        results = self.collection.search(
            data=query_embeddings,
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["chunk_uuid", "page_uuid", "index", "content"],
        )

        if not isinstance(results, SearchResult):
            logger.error("Unexpected result type from search.")
            return

        for hits in results:
            for i, hit in enumerate(hits, 1):
                logger.info(f"Result {i}:")
                logger.info(f"  Score: {hit.distance}")
                logger.info(f"  Chunk UUID: {hit.entity.get('chunk_uuid')}")
                logger.info(f"  Page UUID: {hit.entity.get('page_uuid')}")
                logger.info(f"  Index: {hit.entity.get('index')}")
                logger.info(f"  Content: {hit.entity.get('content')}")
                logger.info("---")

        return hits

    def clear(self):
        """
        Rebuild the collection by dropping and recreating it.
        """
        self.drop()
        self.init()

    def drop(self):
        """
        Delete the collection and all its data from Milvus.
        """
        if utility.has_collection(self.collection_name):
            collection = Collection(self.collection_name)
            collection.drop()
            logger.info(f"Collection '{self.collection_name}' dropped successfully.")
        else:
            logger.info(f"Collection '{self.collection_name}' does not exist.")


if __name__ == "__main__":
    chunks = ChunkCollection("chunks_test")

    def menu():
        print("\nvector_db menu:")
        print("1. Insert sample text")
        print("2. Retrieve chunks")
        print("3. Search top K chunks")
        print("4. Initial collection")
        print("5. Drop collection")
        print("6. Rebuild collection")
        print("0. Exit")
        return int(input("Enter your choice: "))

    def test_insert_sample():
        sample_page_uuid = str(uuid.uuid4())
        sample_text = ""
        # open a text file and read it
        with open("./assets/ai-novels/1.md", mode="r") as f:
            sample_text = f.read()
        chunks.write_content(sample_page_uuid, sample_text)

    while True:
        choice = menu()
        if choice == 1:
            test_insert_sample()
        elif choice == 2:
            chunks.retrieve_chunks()
        elif choice == 3:
            top_k = int(input("Enter the number of top results to retrieve: "))
            query_text = input("Enter the query text: ")
            chunks.search_top_k_chunks(top_k, query_text)
        elif choice == 4:
            chunks.init()
        elif choice == 5:
            chunks.drop()
        elif choice == 6:
            chunks.clear()
        elif choice == 0:
            break
        else:
            print("Invalid choice. Please try again.")
