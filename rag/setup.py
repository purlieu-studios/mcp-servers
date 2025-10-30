from setuptools import setup, find_packages

setup(
    name="rag-mcp-server",
    version="0.1.0",
    description="MCP server providing RAG capabilities with Ollama embeddings",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "mcp>=0.9.0",
        "ollama>=0.1.0",
        "faiss-cpu>=1.7.4",
        "watchdog>=3.0.0",
        "numpy>=1.24.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "rag-mcp-server=src.rag_server:main",
        ],
    },
)
