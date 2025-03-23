import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# ✅ Load Embedding Model (Fast & lightweight)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ✅ Church Knowledge Base (Example)
church_info = {
    "services": "Our church services are at 10 AM on Sundays and bible studies on Wednesday at 5pm.",
    "childrens_camp": "The children's camp is after church from 12-1:30pm.",
    "description": "We are a small community church focused on family and outreach.",
    "location": "2915 St Johns Ave, Palatka, FL 32177",
    "pastor": "Our pastor is John Doe, who has been serving for 15 years.",
    "events": "We have Bible study on Wednesdays at 6 PM.",
    "contact": "You can reach us at 386-325-2814.",
    "email": "You can email us at the1stchurchofgod@gmail.com.",
    "website": "Our website is https://www.palatka-firstchurchofgod.org/",
}

# ✅ Convert Data to Vector Embeddings
texts = list(church_info.values())
embeddings = embedding_model.encode(texts)  # Convert text to embeddings
dimension = embeddings.shape[1]

# ✅ Store Embeddings in FAISS
index = faiss.IndexFlatL2(dimension)  # Create FAISS Index
index.add(np.array(embeddings))  # Add embeddings

async def retrieve_info():
    """Retrieve the most relevant church information based on the query."""
    return church_info
