import os
import openai
import requests
import difflib
from thefuzz import fuzz
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List
from langchain.docstore.document import Document
from langchain_community.document_loaders import PDFPlumberLoader, Docx2txtLoader
from langchain_community.chat_models import ChatOpenAI
from langchain_community.vectorstores.chroma import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


class Config:
    model = 'gpt-3.5-turbo'
    llm = ChatOpenAI(model=model, temperature=0)
    embeddings = OpenAIEmbeddings()
    chunk_size = 2000
    chroma_persist_directory = 'chroma_store'
    file_infos_cache = Path('file_infos_cache')
    if not file_infos_cache.exists():
        file_infos_cache.mkdir()


@dataclass
class FileInfo:
    """Contains the name of the File and the associated ExtendedChroma."""
    file_file: str   
    document_search: 'ExtendedChroma'

    def get_document_search(self) -> 'ExtendedChroma':
        return self.document_search

@dataclass
class ExtendedChroma:
    def __init__(self, chroma_instance, document_path: Path):
        self.chroma = chroma_instance
        self.document_path = document_path

    # Proxy any other attribute access to the underlying Chroma instance
    def __getattr__(self, attr):
        return getattr(self.chroma, attr)


class DocumentProcessor:
    def __init__(self, document_browser) -> None:
        self.document_browser = document_browser
        self.chromas = None
    
    def process_document(self):
        chromas = []
        for path in self.document_browser.get_document_paths():
            # Assuming this method returns a Chroma instance for a document
            chroma = self._process_single_document(path)
            chromas.append(chroma)
        self.chromas = chromas
    
    def _process_single_document(self, document_path):
        cfg = Config()
        """
        Processes the document by loading the text from the document. 
        There are two supported formats: pdf and docx. Then it splits 
        the text in large chunks from which then embeddings are extracted.
        :param document_path a path with documents or a string representing that path.
        :return a Chroma wrapper around the embeddings.
        """
        if not isinstance(document_path, Path):
            document_path = Path(document_path)
        if not document_path.exists():
            print(f"The document ({document_path}) does not exist. Please check")
        else:
            print(f"Processing {document_path}")
            # TODO - Don't load from the path, take the file directly
            loader = (PDFPlumberLoader(str(document_path)) if document_path.suffix == ".pdf"
                    else Docx2txtLoader(str(document_path)))
            
            # Create a list of Document objects from our binary file instead
            doc_list: List[Document] = loader.load()
            print(f"Extracted documents: {len(doc_list)}")
            for i, doc in enumerate(doc_list):
                i += 1
                if len(doc.page_content) == 0:
                    print(f"Document has empty page: {i}")
                else:
                    print(f"Page {i} length: {len(doc.page_content)}")
            text_splitter = CharacterTextSplitter(chunk_size=cfg.chunk_size, chunk_overlap=0)
            texts = text_splitter.split_documents(doc_list)
            print(f"[doc-chunk] chunks_created={len(texts)}")  # added logs

            return self.extract_embeddings(texts, document_path)

    def extract_embeddings(self, texts: List[Document], doc_path: Path) -> Chroma:
        cfg = Config()
        """
        Either saves the Chroma embeddings locally or reads them from disk, in case they exist.
        :return a Chroma wrapper around the embeddings.
        """
        embedding_dir = f"{cfg.chroma_persist_directory}/{doc_path.stem}"
        if Path(embedding_dir).exists():
            return ExtendedChroma(Chroma(persist_directory=embedding_dir, embedding_function=cfg.embeddings), doc_path)
        try:
            chroma_instance = Chroma.from_documents(texts, cfg.embeddings, persist_directory=embedding_dir)
            print(f"[doc-embed] embeddings_created={len(texts)}")  # added logs
            docsearch = ExtendedChroma(chroma_instance, doc_path)
            docsearch.persist()
        except Exception as e:
            print(f"[doc-embed] ERROR Exception={type(e).__name__} msg=\"{e}\"")  # added logs
            return None  
        return docsearch
    
    def get_chromas(self):
        return self.chromas

class FileManager:
    def __init__(self, document_processor) -> None:
        self.document_processor = document_processor

    def _extract_file_infos(self):
        file_infos = []
        for chroma in self.document_processor.get_chromas():
            info = FileManager.extract_single_file_info(chroma)  # Use class name for static method call
            file_infos.extend(info)  # Assuming this returns a list of candidates
        
        return file_infos
    
    def extract_single_file_info(chroma):
        cfg = Config()
        file_key = chroma.document_path.stem  # Now using ExtendedChroma's document_path
        docsearch = chroma  # We are not processing the document again as it was processed when creating Chroma.
        print(f"Processed {chroma.document_path}")
        qa = RetrievalQA.from_chain_type(llm=cfg.llm, chain_type="stuff", retriever=docsearch.as_retriever())
        question_list = []
        file_info = FileInfo(file_file=file_key, document_search=docsearch)
        return [file_info]  # returning as a list for consistency.

    def get_retrieval_questions_for_document(self):
        retrieval_qas = []
        for infos in self._extract_file_infos():
            qa = self.get_single_retrieval_qa(infos)  # Use class name for static method call
            retrieval_qas.append(qa)

        self.retrieval_qas = retrieval_qas

    def get_retrieval_qas(self):
        return self.retrieval_qas

    def get_single_retrieval_qa(self, file_info):
        cfg = Config()
        # Assuming FileInfo has a method/property to return the chroma/document processor's output
        docsearch = file_info.get_document_search()  
        if not docsearch:
            return None
        return RetrievalQA.from_chain_type(llm=cfg.llm, chain_type="stuff", retriever=docsearch.as_retriever())

class AnswerRetreival:
    def __init__(self, file_manager) -> None:
        self.file_manager = file_manager

    def get_answers(self, user_question: str):
        """
        Gets answers for a given user's question from document's RetrievalQA systems.
        """
        qas = self.file_manager.get_retrieval_qas()  # added logs
        print(f"[wiki-retrieve] num_qas={len(qas)}")  # added logs
        model_name = getattr(getattr(qas[0], 'llm', None), 'model_name', 'unknown') if qas else 'unknown'  # added logs
        print(f"[wiki-answer] model={model_name}")  # added logs
        answers = []
        for idx, qa in enumerate(qas):
            try:
                # No direct way to get prompt token count from langchain RetrievalQA; skip unless available
                ans = qa.run(user_question)
                answers.append(ans)
            except Exception as e:
                print(f"[wiki-answer] ERROR Exception={type(e).__name__} msg=\"{e}\" qa_idx={idx}")  # added logs
                answers.append(None)
        print(f"[wiki-retrieve] num_answers={len(answers)}")  # added logs
        for i, ans in enumerate(answers):  # added logs
            if isinstance(ans, str):  # added logs
                print(f"[wiki-retrieve] answer_{i}_type=str answer_{i}_len={len(ans)}")  # added logs
            else:  # added logs
                print(f"[wiki-retrieve] answer_{i}_type={type(ans).__name__}")  # added logs
        return answers

# What does doc_name:str = None mean. I know str is type casting but what is the none
# *other_files used to be passed in to the arguements, temporarily phased out
class DocumentBrowser():
    def __init__(self, file_path:str = None) -> None:
        # self.resume_directory_path = os.getenv("DIRECTORY_PATH")
        # self.other_files = other_files
        self.document_paths = []
        if file_path:
            if os.path.exists(file_path):
                self.document_paths = [file_path]
            else:
                print(f"File at {file_path} does not exist")
        # if len(self.other_files) >= 1:
        #     for other_file in self.other_files:
        #         specific_path = os.path.join(self.resume_directory_path, other_file)
        #     if os.path.exists(specific_path):
        #         self.document_paths.append(specific_path)
        #     else:
        #         print(f"Additional document named {other_file} does not exist in the specified directory.")

    def _list_documents(self):
        # Placeholder implementation
        # This function should list all available documents in a directory or a database
        # For this example, I'll just list files in a directory
        print("List of available documents:")
        all_files = os.listdir(self.resume_directory_path)
        for index, file in enumerate(all_files, start=1):
            print(f"{index}. {os.path.basename(file)}")

    def _get_document_paths_for_indices(self, indices: List[int]) -> List[str]:
        # Placeholder implementation
        # This function should return the full paths of the documents based on their indices
        all_files = os.listdir(self.resume_directory_path)
        return [os.path.join(self.resume_directory_path, all_files[i-1]) for i in indices]

    def get_user_selected_documents(self):
        self._list_documents()
        selected = input("Enter the numbers of the documents you want to use, separated by commas: ")
        selected_indices = [int(idx.strip()) for idx in selected.split(",")]
        self.document_paths = self._get_document_paths_for_indices(selected_indices)

    def get_document_paths(self):
        return self.document_paths
    
class WikipediaManager():
    
    WIKIPEDIA_API_ENDPOINT = "https://en.wikipedia.org/w/api.php"
    
    def __init__(self, query_term) -> None:
        self.query_term = query_term
        self.retrieval_qas = None

    def fetch_wikipedia_content(self) -> str:
    # Step 1: Search Wikipedia for the query term using list=search
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": self.query_term,
            "format": "json"
        }
        user_agent = "DocumentInterrogator/1.0 (contact: shayafra@gmail.com) requests/2.32.3"
        headers = {"User-Agent": user_agent}

        try:
            response = requests.get(self.WIKIPEDIA_API_ENDPOINT, params=search_params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                print(f"[wiki-search] No results found for: {self.query_term}")
                return ""

            def _normalize_text(text):
                import string
                return ''.join(c for c in text.lower().strip() if c not in string.punctuation)

            normalized_query = _normalize_text(self.query_term)

            # Step 2: Check top N results for best similarity and normalize input
            SIMILARITY_THRESHOLD = 0.7
            N = 5
            best_result = None
            best_similarity = 0
            best_title = None
            for result in search_results[:N]:
                candidate_title = result.get("title", "")
                normalized_title = _normalize_text(candidate_title)
                similarity = fuzz.token_set_ratio(normalized_query, normalized_title) / 100.0
                print(f"[wiki-fuzzy] token_set_ratio similarity={similarity:.2f} (query='{normalized_query}', title='{normalized_title}')")
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_result = result
                    best_title = candidate_title

            # Step 3: Enforce threshold
            if best_similarity < SIMILARITY_THRESHOLD:
                print(f"[wiki-fuzzy] best similarity below threshold: {best_similarity:.2f} < {SIMILARITY_THRESHOLD}")
                self.fuzzy_match_failed = True
                return "__WIKI_FUZZY_MATCH_FAILED__"

            print(f"[wiki-search] Best result: {best_title} (similarity={best_similarity:.2f})")

            # Step 4: Fetch the extract for the best match
            extract_params = {
                "action": "query",
                "titles": best_title,
                "prop": "extracts",
                "format": "json"
            }
            extract_response = requests.get(self.WIKIPEDIA_API_ENDPOINT, params=extract_params, headers=headers, timeout=10)
            extract_response.raise_for_status()
            extract_data = extract_response.json()
            pages = extract_data.get("query", {}).get("pages", {})
            first_page = next(iter(pages.values()), {})
            wiki_content = first_page.get("extract", "")
            found = bool(wiki_content)
            print(f"[wiki-extract] extract_found={found} char_count={len(wiki_content)}")
            return wiki_content
        except Exception as e:
            print(f"[wiki-fetch] ERROR Exception={type(e).__name__} msg=\"{e}\" query=\"{self.query_term}\"")
            return ""

    def get_retrieval_questions_for_document(self):
        wiki_content = self.fetch_wikipedia_content()
        if wiki_content == "__WIKI_FUZZY_MATCH_FAILED__":
            print("Please write the article title exactly.")  # This should trigger a UI banner
            self.retrieval_qas = None
            return
        if not wiki_content:
            print("Sorry, no content was found for the provided title/subject.")
            self.retrieval_qas = None
            return
        self.retrieval_qas = self.get_retrieval_qa_for_wikipedia_content(wiki_content, self.query_term)

    def get_retrieval_qa_for_wikipedia_content(self, content: str, title: str):
        cfg = Config()   
        # Create a document from the Wikipedia content
        wiki_document = Document(page_content=content)  
        chunks = [wiki_document]  # added logs (single chunk for now)
        print(f"[wiki-chunk] chunks_created={len(chunks)}")  # added logs
        docsearch = DocumentProcessor(None).extract_embeddings(chunks, Path(f"wiki_{title}"))
        if docsearch is None:
            return None       
        return [RetrievalQA.from_chain_type(llm=cfg.llm, chain_type="stuff", retriever=docsearch.as_retriever())]
    
    def get_retrieval_qas(self):
        return self.retrieval_qas
    
class ManagerDriver():
    """ Attempt at building a class for api interaction """
    # as of right now this is not necessary and the program will work without it but it may be needed later depending on implementation so we keeping it
    def get_document_name(self):
        return self.document_browser.get_user_selected_documents()

    def __init__(self, file_path, question) -> None:
        #Our temporary server
        # An in-memory "database" for storing embeddings
        # Key: document_name, Value: embedding
        self.question = question
        self.file_path = file_path
        # self.other_files = other_files
                # cant remember if this was intended as a temporary local db or if it was necessary for general function
        self.embeddings_store = {}

        # this if statement is the same as get_document_name() it is not needed but may be needed depending on implementatino so were keeping it
        # if document_name is None:
        #     self.document_name = self.get_document_name()

                # why dont we use self. for the arguments?
        # Get the document browser class to handle selecting the docs to use
        # if len(self.other_files) >= 1:
        #     self.document_browser = DocumentBrowser(file_path, *self.other_files)
        # else:
        self.document_browser = DocumentBrowser(file_path)

        # Get the document processor class to load and chunk the documents
        self.document_processor = DocumentProcessor(self.document_browser)
        # Get the manager class to search the document data
        self.file_manager = FileManager(self.document_processor)
        # Get the class to manage the answer
        self.get_answer = AnswerRetreival(self.file_manager)

        #creates and stores embedding in database using document given from database
    def create_embedding(self) -> str:
        # Load the document
        #document_broswer has a function called get_user_selected_documents
        #uses prcoess_document from document_processor
        # Parse and embed the document
        embedding = self.document_processor.process_document()
        # Store the embedding in our mock database
        self.embeddings_store[self.file_path] = embedding
        print(embedding)
        return embedding

    def get_embedding(self) -> str:
        # Check if the embedding exists in our mock database
        if self.file_path in self.embeddings_store:
            print(self.embeddings_store[self.file_path])
            return self.embeddings_store[self.file_path]
        # If not, create a new embedding and return it
        return self.create_embedding()

    def make_answer(self) -> str:
        # # Get the document's embedding
        self.get_embedding()
        #Doesn't this need to be changed to take the embeddings as an input? TBH this function confuses me
        self.file_manager.get_retrieval_questions_for_document()
        answer = self.get_answer.get_answers(self.question)
        return answer
        

class WikiDriver(ManagerDriver):
    """ Search Wikipedia """
    def __init__(self, wikiTitle, question) -> None:
        # Get the input criteria for searching for the doc and saves question
        self.wikiUrl = wikiTitle
        self.question = question       
        # Get the manager class to get the document data
        self.file_manager = WikipediaManager(wikiTitle)
        # Get the class to manage the answer
        self.answer = AnswerRetreival(self.file_manager)

    def run_analysis(self):
        # Calls the "manager" class we created (WikipediaManager) to get
        # the parameters used to search for document we want to ask 
        # questions about
        self.file_manager.get_retrieval_questions_for_document()

        # Create the answer to questions about the document
        self.answer.get_answers(self.question)


def main():
    # Create the core driver that lets us select functionality
    
    # single document test
    driver = ManagerDriver("Harilal Shah.docx", "What is the applicants name?")
    
    # multi doc test
    # driver = ManagerDriver("Harilal Shah.docx", "What is the applicants name?", "Gil Fernandes.pdf")
    
    #wiki search test
    # driver = WikiDriver("Elephants", "How big do Elephants get?")

    # run_analysis() is essentially the main method for this class
    driver.make_answer()
    # driver.get_embedding()
    # driver.create_embedding()


if __name__ == "__main__":
    main()