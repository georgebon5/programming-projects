text = """Machine Learning Fundamentals:
Supervised learning uses labeled data to train models. Common algorithms include linear regression, decision trees, and neural networks.
Unsupervised learning finds patterns in unlabeled data. Clustering and dimensionality reduction are key techniques.

Deep Learning:
Deep learning uses artificial neural networks with multiple layers. Convolutional Neural Networks (CNNs) excel at image recognition.
Recurrent Neural Networks (RNNs) and Transformers are used for sequence data like text and time series.

Natural Language Processing:
NLP enables computers to understand, interpret, and generate human language.
Large Language Models (LLMs) like GPT-4 are trained on massive text corpora.
RAG (Retrieval-Augmented Generation) enhances LLM responses by providing relevant context from a knowledge base.

Vector Databases:
Vector databases store high-dimensional embeddings that represent text, images, or other data.
Similarity search finds the most relevant vectors using distance metrics like cosine similarity.
ChromaDB and Pinecone are popular vector database solutions.

Multi-Tenant Architecture:
Multi-tenancy allows a single application to serve multiple organizations called tenants.
Data isolation between tenants is critical for security and compliance.
Each tenant's documents and queries must be strictly separated.
"""

with open("/tmp/ai_knowledge.txt", "w") as f:
    f.write(text)
print(f"Created {len(text)} chars")
