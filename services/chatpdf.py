from langchain_community.document_loaders import PyPDFLoader
from models.api import FileChatReq

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

DB_NAME = "./db/chroma_db"


async def feed_data(file_path: str) -> str:
    # document loader to load data
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    # text split by characters
    text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=0)
    split_docs = text_splitter.split_documents(documents)
    # text embedding by model
    embeddings = OpenAIEmbeddings()

    # persist embedding by db(chromadb)
    docsearch = Chroma.from_documents(split_docs, embeddings, persist_directory=DB_NAME)
    docsearch.persist()

    return text_summarize()


async def pdf_chat(req: FileChatReq):
    # load embedding from db
    embeddings = OpenAIEmbeddings()
    docsearch = Chroma(persist_directory=DB_NAME, embedding_function=embeddings)
    # create LLM
    llm = OpenAI(temperature=0, verbose=True, max_tokens=1000)
    # create a retrievers to QA
    qa = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=docsearch.as_retriever()
    )
    result = qa.run(req.message)

    # to use long context chat, see: https://python.langchain.com/docs/modules/data_connection/retrievers/long_context_reorder
    return {"response": result}


async def text_summarize(docs):
    # Define prompt
    prompt_template = """Write a concise summary of the following:
    "{text}"
    CONCISE SUMMARY:"""
    prompt = PromptTemplate.from_template(prompt_template)

    # Define LLM chain
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k")
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    # Define StuffDocumentsChain
    stuff_chain = StuffDocumentsChain(
        llm_chain=llm_chain, document_variable_name="text"
    )
    return stuff_chain.run(docs)
