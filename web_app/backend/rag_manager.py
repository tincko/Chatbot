import os
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import pypdf

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

    def _extract_text_from_pdf(self, filepath):
        text = ""
        try:
            reader = pypdf.PdfReader(filepath)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF {filepath}: {e}")
        return text

    def _extract_text_from_txt(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT {filepath}: {e}")
            return ""

    def _chunk_text(self, text, chunk_size=1000, overlap=200):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        return chunks

    def add_document(self, filename, filepath, chunk_size=1000, overlap=200):
        # Remove existing chunks for this file first to avoid duplicates if re-uploading
        self.delete_document(filename)

        if filename.lower().endswith('.pdf'):
            text = self._extract_text_from_pdf(filepath)
        else:
            text = self._extract_text_from_txt(filepath)

        if not text.strip():
            return False

        chunks = self._chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        
        ids = [f"{filename}_{i}" for i in range(len(chunks))]
        metadatas = [{"filename": filename, "chunk_index": i} for i in range(len(chunks))]

        if chunks:
            self.collection.add(
                documents=chunks,
                ids=ids,
                metadatas=metadatas
            )
        return True

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
