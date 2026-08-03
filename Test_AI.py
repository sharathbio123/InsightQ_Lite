import os
import glob

# LangChain core modules
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

# LangChain Community & Integration Modules
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama

def setup_rag_pipeline(pdf_folder_path):
    print(f"🔄 Step 1: Scanning for PDF documents in:\n   -> {pdf_folder_path}")
    
    pdf_files = glob.glob(os.path.join(pdf_folder_path, "*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(
            f"❌ No PDF files found!\n"
            f"   Please ensure the folder exists at:\n"
            f"   -> '{pdf_folder_path}'\n"
            f"   and that it contains at least one PDF document."
        )
    
    docs = []
    for pdf in pdf_files:
        print(f"📄 Loading: {os.path.basename(pdf)}")
        loader = PyPDFLoader(pdf)
        docs.extend(loader.load())
        
    print(f"📦 Successfully loaded {len(docs)} total pages.")

    print("\n✂️ Step 2: Splitting text into manageable chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    print(f"\n🧠 Step 3: Generating local vector embeddings (using nomic-embed-text)...")
    embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_BASE_URL)
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4}) 

    print(f"\n🤖 Step 4: Initializing local LLM (llama3.2:3b)...")
    llm = ChatOllama(model="llama3.2:3b", temperature=0.2, base_url=OLLAMA_BASE_URL)

    # Chatbot Prompt Setup with a placeholder for structural memory
    system_prompt = (
        "You are an expert conversational research assistant for scientific documents.\n"
        "Answer the user's question using ONLY the provided context below. "
        "Maintain a helpful, conversational chatbot tone. "
        "If you do not know the answer or if it's not in the context, say that you cannot "
        "find it in the documents. Do not invent facts.\n\n"
        "Context:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"), # Tracks conversation flow
        ("human", "{input}"),
    ])

    def format_docs(docs_list):
        return "\n\n".join(doc.page_content for doc in docs_list)

    # Chatbot generation pipeline matching inputs dynamically
    # FIXED: Extracting x["input"] explicitly before passing to the retriever
    rag_chain = (
        {
            "context": (lambda x: x["input"]) | retriever | format_docs, 
            "input": lambda x: x["input"],
            "chat_history": lambda x: x["chat_history"]
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("\n✅ Setup Complete! Your offline Chatbot is ready.")
    return rag_chain
    
if __name__ == "__main__":
    # Notebook/VS Code interactive safety check for paths
    try:
        script_directory = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_directory = os.getcwd()
        
    target_pdf_folder = os.path.join(script_directory, "documents")
    
    # Auto-create the folder for convenience if it doesn't exist yet
    if not os.path.exists(target_pdf_folder):
        os.makedirs(target_pdf_folder)
        print(f"📁 Created missing folder: '{target_pdf_folder}'")
        print("👉 Please drop your PDF documents inside it and run this script again!")
        exit()
    
    try:
        pipeline = setup_rag_pipeline(target_pdf_folder)
        
        # Local array to store memory threads while the script runs
        chat_history = []
        
        print("\n💬 EXOSOME CHATBOT ACTIVE (Type 'exit' to close)")
        print("="*50)
        
        while True:
            query = input("\n👤 You: ")
            if query.lower() in ['exit', 'quit']:
                print("Exiting chat. Goodbye!")
                break
                
            if not query.strip():
                continue
                
            print("⏳ Chatbot is reading context...")
            
            # Run the pipeline passing the question AND the ongoing memory
            response = pipeline.invoke({
                "input": query,
                "chat_history": chat_history
            })
            
            print(f"\n🤖 AI: {response}")
            print("-" * 50)
            
            # Save the turn to chat memory
            chat_history.append(HumanMessage(content=query))
            chat_history.append(AIMessage(content=response))
            
            # Limit memory to last 6 messages to keep context window clean
            if len(chat_history) > 6:
                chat_history = chat_history[-6:]
            
    except Exception as e:
        print(f"\n❌ Error encountered: {e}")
