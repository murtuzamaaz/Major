"""
Improved query service with multi-stage retrieval and intelligent ranking.
- Retrieves semantically relevant chunks
- Ranks by relevance and type
- Provides rich context to LLM
- Generates better prompts
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path
import json

from backend.app.services.code_assist.improved_vector_store_service import load_index
from backend.app.core.ollama_client import generate, embed


class RetrievalResult:
    """Represents a single retrieved and ranked result."""
    
    def __init__(
        self,
        chunk: Dict,
        similarity_score: float,
        boost_score: float,
        rank: int,
        relevance_reason: str
    ):
        self.chunk = chunk
        self.similarity_score = float(similarity_score)  # Ensure Python float
        self.boost_score = float(boost_score)  # Ensure Python float
        self.final_score = float(self.similarity_score * self.boost_score)  # Convert to Python float
        self.rank = rank
        self.relevance_reason = relevance_reason


def multi_stage_retrieval(
    repo_id: str,
    query: str,
    top_k: int = 10,
    include_readme: bool = True
) -> List[RetrievalResult]:
    """
    Perform multi-stage retrieval with intelligent ranking.
    
    Stages:
    1. Semantic search via vector similarity
    2. Keyword matching
    3. Metadata filtering
    4. Intelligent ranking and scoring
    5. Result diversification
    """
    
    try:
        index, metadata = load_index(repo_id)
    except FileNotFoundError:
        return []
    
    # === STAGE 1: Vector-based semantic search ===
    query_vector = embed(query)
    if not isinstance(query_vector, list):
        return []
    
    distances, indices = index.search(
        np.array([query_vector]).astype("float32"),
        min(top_k * 3, len(metadata))  # Get more to filter/rank
    )
    
    candidates: List[Tuple[Dict, float, str]] = []
    
    for distance, idx in zip(distances[0], indices[0]):
        if idx >= len(metadata):
            continue
        
        chunk = metadata[idx]
        similarity_score = float(1 / (1 + float(distance)))  # Convert to Python float
        relevance_reason = "semantic_match"
        
        candidates.append((chunk, similarity_score, relevance_reason))
    
    # === STAGE 2: Keyword matching (bonus scoring) ===
    query_terms = set(query.lower().split())
    query_terms = {t for t in query_terms if len(t) > 3}  # Filter short words
    
    for i, (chunk, sim_score, reason) in enumerate(candidates):
        chunk_text = chunk.get('text', '').lower()
        chunk_name = chunk.get('name', '').lower()
        
        # Count keyword matches
        keyword_matches = sum(1 for term in query_terms if term in chunk_text or term in chunk_name)
        
        if keyword_matches > 0:
            boost = 1 + (keyword_matches * 0.05)
            candidates[i] = (chunk, sim_score * boost, "keyword_match")
    
    # === STAGE 3: Metadata-based relevance boosting ===
    results: List[RetrievalResult] = []
    
    for chunk, similarity, reason in candidates:
        metadata_obj = chunk.get('metadata', {})
        boost = 1.0
        
        # Boost important chunk types
        chunk_type = metadata_obj.get('chunk_type', '')
        type_boosts = {
            'class': 1.3,
            'function': 1.2,
            'method': 1.2,
            'markdown_section': 1.1,
            'file_docstring': 1.1,
            'imports': 1.0,
            'code_block': 0.9
        }
        boost *= type_boosts.get(chunk_type, 1.0)
        
        # Boost by relevance patterns
        patterns = metadata_obj.get('patterns', [])
        for pattern in patterns:
            if pattern in query.lower():
                boost *= 1.15
        
        final_score = similarity * boost
        
        result = RetrievalResult(
            chunk=chunk,
            similarity_score=similarity,
            boost_score=boost,
            rank=len(results),
            relevance_reason=reason
        )
        results.append(result)
    
    # === STAGE 4: Intelligent ranking ===
    results.sort(key=lambda r: r.final_score, reverse=True)
    
    # === STAGE 5: Result diversification ===
    # Avoid returning too many chunks from same file/class
    diversified = []
    seen_sources = {}
    
    for result in results:
        source = result.chunk.get('name', '').split('::')[0]  # Get file
        
        # Limit chunks per source to 3
        if seen_sources.get(source, 0) < 3:
            diversified.append(result)
            seen_sources[source] = seen_sources.get(source, 0) + 1
        
        if len(diversified) >= top_k:
            break
    
    # === STAGE 6: Include README context if available ===
    if include_readme and len(diversified) < top_k:
        readme_chunks = [c for c in metadata if 'README' in c.get('name', '')]
        for chunk in readme_chunks[:2]:
            if not any(r.chunk == chunk for r in diversified):
                diversified.append(RetrievalResult(
                    chunk=chunk,
                    similarity_score=0.7,  # Lower but guaranteed inclusion
                    boost_score=1.2,
                    rank=len(diversified),
                    relevance_reason="project_context"
                ))
    
    return diversified[:top_k]


def build_context_from_results(results: List[RetrievalResult]) -> str:
    """
    Build a rich context string from retrieved chunks.
    Organizes chunks by type and includes metadata.
    """
    
    if not results:
        return "No relevant code found."
    
    # Organize by chunk type
    organized: Dict[str, List[RetrievalResult]] = {}
    for result in results:
        chunk_type = result.chunk.get('metadata', {}).get('chunk_type', 'unknown')
        if chunk_type not in organized:
            organized[chunk_type] = []
        organized[chunk_type].append(result)
    
    context_parts = []
    
    # Add README/project context first
    for chunk_type in ['markdown_section', 'file_docstring', 'project_metadata']:
        if chunk_type in organized:
            context_parts.append(f"\n## Project Context\n")
            for result in organized[chunk_type][:2]:
                chunk = result.chunk
                text = chunk.get('text', '')
                context_parts.append(f"```markdown\n{text}\n```\n")
    
    # Add class definitions
    if 'class' in organized:
        context_parts.append(f"\n## Class Definitions\n")
        for result in organized['class'][:3]:
            chunk = result.chunk
            name = chunk.get('name', 'Unknown')
            metadata = chunk.get('metadata', {})
            context = chunk.get('context', {})
            
            context_parts.append(f"### {name}\n")
            if context.get('description'):
                context_parts.append(f"Description: {context['description']}\n")
            if context.get('methods'):
                context_parts.append(f"Methods: {', '.join(context['methods'][:5])}\n")
            
            context_parts.append(f"```python\n{chunk.get('text', '')}\n```\n")
    
    # Add function definitions
    if 'function' in organized or 'method' in organized:
        context_parts.append(f"\n## Functions and Methods\n")
        for chunk_type in ['function', 'method']:
            if chunk_type in organized:
                for result in organized[chunk_type][:5]:
                    chunk = result.chunk
                    name = chunk.get('name', 'Unknown')
                    context = chunk.get('context', {})
                    
                    context_parts.append(f"### {name}\n")
                    if context.get('description'):
                        context_parts.append(f"Description: {context['description']}\n")
                    if context.get('parameters'):
                        context_parts.append(f"Parameters: {', '.join(context['parameters'][:5])}\n")
                    
                    context_parts.append(f"```\n{chunk.get('text', '')}\n```\n")
    
    # Add imports and dependencies
    if 'imports' in organized:
        context_parts.append(f"\n## Dependencies\n")
        for result in organized['imports'][:2]:
            context_parts.append(f"```\n{result.chunk.get('text', '')}\n```\n")
    
    # Add any remaining chunks
    for chunk_type, results_list in organized.items():
        if chunk_type not in ['markdown_section', 'file_docstring', 'class', 'function', 'method', 'imports']:
            context_parts.append(f"\n## {chunk_type.title()}\n")
            for result in results_list[:2]:
                context_parts.append(f"```\n{result.chunk.get('text', '')}\n```\n")
    
    return ''.join(context_parts)


def build_intelligent_prompt(
    query: str,
    context: str,
    repo_profile: Optional[Dict] = None
) -> str:
    """
    Build an intelligent prompt with rich context and instructions.
    """
    
    system_instruction = """You are an expert code assistant helping developers understand and work with a codebase.

Your responsibilities:
1. Explain code clearly and accurately
2. Point out important patterns and best practices
3. Suggest improvements when appropriate
4. Clarify architecture and design decisions
5. Help with debugging and feature implementation

Be specific - reference actual code snippets and line numbers when possible.
Be honest - if something is unclear or missing, say so."""
    
    repo_context = ""
    if repo_profile:
        repo_context = f"""
## Repository Overview
- Name: {repo_profile.get('repo_name', 'Unknown')}
- Primary Language: {', '.join(repo_profile.get('languages', ['Unknown'])[:3])}
- Main Purpose: {repo_profile.get('description', 'Not provided')}
"""
    
    prompt = f"""{system_instruction}

{repo_context}

## Codebase Context
The following is relevant code from the repository:

{context}

## Your Task
Answer the following question about the codebase:

{query}

Provide a clear, detailed response that:
1. Directly answers the question
2. References specific code and files
3. Explains the "why" behind the implementation
4. Suggests improvements if relevant
5. Points out related code that might be useful"""
    
    return prompt


def ask_question(repo_id: str, question: str, model: str = "deepseek-coder:6.7b") -> Dict:
    """
    Answer a question about the codebase using multi-stage retrieval and intelligent prompting.
    """
    
    print(f"\n🔍 Analyzing question: {question}")
    
    # === Stage 1: Multi-stage retrieval ===
    print("📚 Retrieving relevant code...")
    results = multi_stage_retrieval(repo_id, question, top_k=10)
    
    if not results:
        return {
            "answer": "I couldn't find relevant code to answer your question. Try asking about specific files or functions.",
            "sources": [],
            "status": "no_results"
        }
    
    print(f"✓ Found {len(results)} relevant chunks")
    
    # === Stage 2: Build context ===
    print("🔗 Building context...")
    context = build_context_from_results(results)
    
    # === Stage 3: Build intelligent prompt ===
    print("🧠 Generating prompt...")
    prompt = build_intelligent_prompt(question, context)
    
    # === Stage 4: Generate response ===
    print("⚙️  Calling LLM...")
    try:
        response = generate(model, prompt)
    except Exception as e:
        return {
            "answer": f"Error generating response: {str(e)}",
            "sources": [],
            "status": "error"
        }
    
    # === Stage 5: Extract sources ===
    sources = [r.chunk.get('name', 'Unknown') for r in results[:5]]
    
    print("✓ Response generated")
    
    return {
        "answer": response,
        "sources": sources,
        "status": "success",
        "retrieved_chunks": len(results),
        "top_matches": [
            {
                "name": r.chunk.get('name'),
                "type": r.chunk.get('metadata', {}).get('chunk_type'),
                "score": float(r.final_score),  # Convert numpy float to Python float
                "reason": r.relevance_reason
            }
            for r in results[:3]
        ]
    }


__all__ = [
    'multi_stage_retrieval',
    'build_context_from_results',
    'build_intelligent_prompt',
    'ask_question',
    'RetrievalResult'
]