import os
import chromadb
from chromadb.utils import embedding_functions
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

class RAGManager:
    def __init__(self, persistence_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persistence_directory)
        # Use a lightweight model for local embeddings
        self.embedding_model_name = "all-MiniLM-L6-v2"
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.embedding_model_name)
        
        self.collection = self.client.get_or_create_collection(
            name="documents",
            embedding_function=self.embedding_function
        )
        
        # Initialize Docling
        self.doc_converter = DocumentConverter()

    def add_document(self, filename, filepath, chunk_size=1000, overlap=200):
        # Remove existing chunks for this file first to avoid duplicates if re-uploading
        self.delete_document(filename)

        try:
            # Convert document using Docling
            conv_result = self.doc_converter.convert(filepath)
            doc = conv_result.document
            
            # Chunk the document
            # We use HybridChunker with the requested chunk_size (max_tokens)
            # Note: HybridChunker might not support 'overlap' directly in all versions, 
            # but it handles semantic boundaries well.
            chunker = HybridChunker(max_tokens=chunk_size)
            chunk_iter = chunker.chunk(doc)
            
            chunks = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunk_iter):
                chunks.append(chunk.text)
                meta = {
                    "filename": filename,
                    "chunk_index": i
                }
                metadatas.append(meta)
                ids.append(f"{filename}_{i}")

            if chunks:
                self.collection.add(
                    documents=chunks,
                    ids=ids,
                    metadatas=metadatas
                )
            return True

        except Exception as e:
            print(f"Error processing document {filename} with Docling: {e}")
            return False

    def delete_document(self, filename):
        try:
            self.collection.delete(where={"filename": filename})
        except Exception as e:
            print(f"Error deleting document {filename}: {e}")

    def query(self, query_text, n_results=3, filter_filenames=None):
        where_filter = None
        if filter_filenames:
            if len(filter_filenames) == 1:
                where_filter = {"filename": filter_filenames[0]}
            else:
                where_filter = {"filename": {"$in": filter_filenames}}

        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )
        
        # Flatten results
        documents = results['documents'][0] if results['documents'] else []
        return documents

    def clear_collection(self):
        try:
            # Delete all items
            self.client.delete_collection("documents")
            # Re-create
            self.collection = self.client.get_or_create_collection(
                name="documents",
                embedding_function=self.embedding_function
            )
        except Exception as e:
            print(f"Error clearing collection: {e}")
