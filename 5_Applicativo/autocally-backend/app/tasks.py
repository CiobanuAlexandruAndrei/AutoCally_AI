from .celery_app import celery
from .extensions import db
from .base_knowledge.models import TaskStatusBaseKnowledge, BaseKnowledge, BaseKnowledgeFile
from celery.utils.log import get_task_logger
from datetime import datetime
from pathlib import Path
from .config import BASE_DIR
import time
import eventlet
# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import (
    TextLoader, 
    DirectoryLoader, 
    PyPDFLoader, 
    UnstructuredPDFLoader
)
import os
import json
import redis
from openai import OpenAI
from .config import Config
from multiprocessing import Pool, cpu_count
from functools import partial
import concurrent.futures

logger = get_task_logger(__name__)


@celery.task(bind=True)
def process_base_knowledge(self, base_knowledge_id):
    start_time = time.time()
    logger.info(f"Starting process_base_knowledge task for base_knowledge_id: {base_knowledge_id}")
    
    session = db.session
    task_status = None
    
    try:
        # Initialize task status
        task_status = TaskStatusBaseKnowledge(
            task_id=self.request.id,
            status='STARTED',
            progress=0,
            total_steps=4,
            base_knowledge_id=base_knowledge_id
        )
        session.add(task_status)
        session.commit()

        base_knowledge = session.query(BaseKnowledge).get(base_knowledge_id)
        if not base_knowledge:
            raise ValueError(f"Base knowledge {base_knowledge_id} not found")

        # Step 1: Document loading - avoid ProcessPoolExecutor for now
        task_status.status_message = "Loading documents"
        task_status.progress = 1
        session.commit()

        documents = []
        files_path = Path(BASE_DIR) / base_knowledge.folder_path / 'files'
        
        # Process files sequentially for now
        for file in base_knowledge.files:
            file_path = files_path / file.name
            try:
                if file.file_type == 'pdf':
                    loader = PyPDFLoader(str(file_path))
                    documents.extend(loader.load())
                elif file.file_type == 'txt':
                    loader = TextLoader(str(file_path))
                    documents.extend(loader.load())
            except Exception as e:
                logger.error(f"Error loading file {file.name}: {str(e)}")

        # Step 2: Document splitting - use single-threaded approach for debugging
        task_status.status_message = "Splitting documents"
        task_status.progress = 2
        session.commit()

        # Optimize chunk size based on document length
        avg_doc_length = sum(len(doc.page_content) for doc in documents) / len(documents) if documents else 1000
        chunk_size = min(max(int(avg_doc_length / 3), 500), 2000)  # Dynamic chunk size between 500-2000

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=int(chunk_size * 0.1),
            length_function=len
        )

        # Process documents sequentially
        splits = []
        for doc in documents:
            splits.extend(text_splitter.split_documents([doc]))

        # Step 3 & 4: Embedding creation and storage
        task_status.status_message = "Creating embeddings and storing"
        task_status.progress = 3
        session.commit()

        persist_dir = Path(BASE_DIR) / base_knowledge.folder_path / 'chroma_db'
        persist_dir.mkdir(exist_ok=True)

        batch_size = 50
        embeddings = OpenAIEmbeddings()
        vectorstore = Chroma(
            persist_directory=str(persist_dir),
            embedding_function=embeddings
        )

        for i in range(0, len(splits), batch_size):
            batch = splits[i:i + batch_size]
            vectorstore.add_documents(documents=batch)
            
            # Update progress
            progress = min(3 + ((i + batch_size) / len(splits)), 4)
            task_status.progress = progress
            session.commit()

        vectorstore.persist()

        # Update completion status
        base_knowledge.last_loaded = datetime.now()
        base_knowledge.needs_reload = False
        task_status.status = 'SUCCESS'
        task_status.progress = task_status.total_steps
        session.commit()

        total_time = time.time() - start_time
        logger.info(f"Task completed successfully. Total execution time: {total_time:.2f} seconds")
        return {'status': 'success', 'processing_time': total_time}

    except Exception as e:
        logger.error(f"Error processing base knowledge: {str(e)}", exc_info=True)
        if task_status:
            task_status.status = 'FAILURE'
            task_status.error = str(e)
            session.commit()
        return {'status': 'error', 'message': str(e)}
    finally:
        session.close()
        