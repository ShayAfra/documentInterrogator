from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores.chroma import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from .processor import DocxProcessor, PDFProcessor
    
class EmbeddingManager():
    ''' Manages operations related to embeddings like creating them or getting an answer from them '''
    
    def __init__(self, file_name, file_contents, model='gpt-3.5-turbo', chunk_size=2000) -> None:
        self.file_name = file_name
        self.file_suffix =  file_name.rsplit('.', 1)[1].lower() 
        self.file_contents = file_contents
        
        self.chunk_size = chunk_size
        self.llm = ChatOpenAI(model=model, temperature=0)
        self.embeddings_client = OpenAIEmbeddings()

    def _get_chroma_embeddings(self) -> Chroma:
        ''' Get a ChromaDB VectorStore with the contents of the passed file
            
            This is done based on the file extension
        '''

        processor = None
        if self.file_suffix == "pdf":
            processor = PDFProcessor(self.file_name, self.file_contents)
        elif self.file_suffix == "docx":
            processor = DocxProcessor(self.file_name, self.file_contents)
        else:
            # If just a text file this is sufficient
            return Chroma.from_texts([self.file_contents], self.embeddings_client)
        
        # Otherwise more work to do
        doc_list = processor.process()
        text_splitter = CharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=0)
        texts = text_splitter.split_documents(doc_list)
        
        return Chroma.from_documents(texts, self.embeddings_client)

    def get_answer(self, question) -> str:
        ''' Answer a question about the passed document '''

        # Get the embeddings based on the stored file contents
        embeddings = self._get_chroma_embeddings()

        # Get an LLM retriver to act on our embeddings
        retriever = RetrievalQA.from_chain_type(llm=self.llm, retriever=embeddings.as_retriever())

        # Send our question to the retriever and get the answer
        try:
            answer = retriever({"query": question})
        except Exception as e:
            # Check for context_length_exceeded error from OpenAI
            if hasattr(e, 'args') and e.args and 'context length' in str(e.args[0]).lower():
                return {"error": "oversized_file", "message": "AI models can only process a certain amount of text at once. Please use a smaller file."}
            # You can add more fine-grained error checks here if needed
            raise

        if answer:
            return answer['result']
