"""
Improved embedding service with semantic context enrichment.
Enriches chunks with code analysis metadata before embedding.
"""

from typing import Dict, List, Optional
import re
from backend.app.core.ollama_client import embed


def extract_semantic_metadata(chunk: Dict) -> Dict:
    """
    Extract semantic metadata from a code chunk for richer embeddings.
    Returns structured metadata that will be included in embedding context.
    """
    metadata = {
        'chunk_type': chunk.get('chunk_type'),
        'name': chunk.get('name'),
        'language': chunk.get('language'),
        'file_path': chunk.get('file_path', ''),
        'risk_level': chunk.get('risk_level', 'low'),
        'keywords': [],
        'dependencies': [],
        'public_api': [],
        'complexity': 'low',
        'imports': [],
        'annotations': []
    }
    
    text = chunk.get('text', '').lower()
    full_text = chunk.get('text', '')
    
    # === Extract keywords from code ===
    code_keywords = {
        'async', 'await', 'class', 'function', 'def', 'return', 'if', 'for', 'while',
        'try', 'except', 'finally', 'import', 'from', 'export', 'const', 'let', 'var',
        'interface', 'type', 'enum', 'decorator', '@', 'property', 'staticmethod',
        'classmethod', 'raise', 'yield', 'lambda', 'switch', 'case'
    }
    
    for keyword in code_keywords:
        if keyword in text:
            metadata['keywords'].append(keyword)
    
    # === Extract import/dependency statements ===
    import_pattern = r'(?:from|import)\s+[\w._]+|require\(["\'][\w._/]+["\']\)'
    imports = re.findall(import_pattern, full_text, re.IGNORECASE)
    metadata['imports'] = imports[:5]  # Top 5 imports
    
    # === Extract function/class names (public API) ===
    if chunk.get('chunk_type') in {'class', 'function', 'method'}:
        name_parts = chunk.get('name', '').split('::')
        if len(name_parts) >= 2:
            metadata['public_api'] = [name_parts[-1]]
    
    # === Estimate complexity based on code characteristics ===
    complexity_score = 0
    complexity_score += text.count('if ') * 2
    complexity_score += text.count('for ') * 2
    complexity_score += text.count('while ') * 2
    complexity_score += text.count('try') * 1
    complexity_score += text.count('lambda') * 1
    complexity_score += text.count('async') * 1
    
    if complexity_score > 15:
        metadata['complexity'] = 'high'
    elif complexity_score > 5:
        metadata['complexity'] = 'medium'
    else:
        metadata['complexity'] = 'low'
    
    # === Extract decorators/annotations ===
    decorator_pattern = r'@\w+|:\s*\w+(?:\[.*?\])?'
    decorators = re.findall(decorator_pattern, full_text)
    metadata['annotations'] = list(set(decorators))[:5]
    
    # === Detect patterns and add context ===
    patterns_detected = []
    
    if 'def __init__' in full_text or 'constructor' in text:
        patterns_detected.append('initialization')
    if 'test' in chunk.get('name', '').lower():
        patterns_detected.append('test_code')
    if 'exception' in text or 'error' in text:
        patterns_detected.append('error_handling')
    if 'api' in text or 'endpoint' in text:
        patterns_detected.append('api_handler')
    if 'database' in text or 'query' in text or 'sql' in text:
        patterns_detected.append('database_interaction')
    if 'authentication' in text or 'auth' in text:
        patterns_detected.append('authentication')
    if 'logging' in text or 'log' in text:
        patterns_detected.append('logging')
    
    metadata['patterns'] = patterns_detected
    
    return metadata


def generate_enriched_embedding_text(chunk: Dict, metadata: Dict) -> str:
    """
    Generate an enriched text representation that combines code with semantic context.
    This text will be embedded, making the embedding more semantically aware.
    """
    
    # Build prefix with context information
    prefix_parts = []
    
    # Add chunk type and name
    chunk_type = metadata.get('chunk_type', 'code')
    name = metadata.get('name', 'unnamed')
    prefix_parts.append(f"[{chunk_type.upper()}: {name}]")
    
    # Add description from context if available
    context = chunk.get('context', {})
    if context.get('description'):
        prefix_parts.append(f"Description: {context.get('description')}")
    
    # Add API signature for functions/methods
    if metadata.get('public_api'):
        prefix_parts.append(f"API: {', '.join(metadata['public_api'])}")
    
    # Add parameters for functions
    if 'parameters' in context:
        params = context.get('parameters', [])
        if params:
            prefix_parts.append(f"Parameters: {', '.join(params)}")
    
    # Add related patterns
    if metadata.get('patterns'):
        prefix_parts.append(f"Patterns: {', '.join(metadata['patterns'])}")
    
    # Add dependencies
    if metadata.get('imports'):
        prefix_parts.append(f"Imports: {', '.join(metadata['imports'][:3])}")
    
    # Combine everything
    prefix = '\n'.join(prefix_parts)
    code = chunk.get('text', '')
    
    enriched_text = f"{prefix}\n\n{code}"
    
    return enriched_text


def embed_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    Embed a list of chunks with semantic enrichment.
    Returns chunks with embedding vectors attached.
    """
    enriched = []
    
    for chunk in chunks:
        text = chunk.get("text", "").strip()
        
        # Skip empty chunks
        if not text:
            continue
        
        try:
            # Extract semantic metadata
            metadata = extract_semantic_metadata(chunk)
            
            # Generate enriched text for embedding
            enriched_text = generate_enriched_embedding_text(chunk, metadata)
            
            # Generate embedding using Ollama
            vector = embed(enriched_text)
            
            # Validate embedding
            if not isinstance(vector, list) or len(vector) != 768:
                print(f"Skipping {chunk.get('name')} - invalid embedding dimension")
                continue
            
            # Attach metadata and embedding to chunk
            chunk['embedding'] = vector
            chunk['metadata'] = metadata
            chunk['enriched_text'] = enriched_text
            chunk['token_count'] = len(enriched_text.split())
            
            enriched.append(chunk)
            
            print(f"✓ Embedded {chunk.get('name')} ({metadata.get('chunk_type')})")
            
        except Exception as e:
            print(f"✗ Failed to embed {chunk.get('name')}: {e}")
            continue
    
    print(f"\nTotal chunks embedded: {len(enriched)}")
    return enriched


def boost_embedding_score(chunk: Dict, query: str, base_score: float) -> float:
    """
    Apply semantic boosting to embedding similarity scores.
    Boosts scores for semantically relevant matches.
    """
    boosted_score = base_score
    
    query_lower = query.lower()
    metadata = chunk.get('metadata', {})
    
    # Boost if chunk type is relevant
    chunk_type = metadata.get('chunk_type', '')
    if chunk_type in {'class', 'function', 'method'}:
        # Code structure chunks are more relevant than random code blocks
        boosted_score *= 1.15
    
    # Boost if patterns match query intent
    if 'test' in query_lower and 'test_code' in metadata.get('patterns', []):
        boosted_score *= 1.25
    
    if 'database' in query_lower and 'database_interaction' in metadata.get('patterns', []):
        boosted_score *= 1.20
    
    if 'api' in query_lower and 'api_handler' in metadata.get('patterns', []):
        boosted_score *= 1.20
    
    if 'error' in query_lower and 'error_handling' in metadata.get('patterns', []):
        boosted_score *= 1.20
    
    # Boost by complexity if query seems advanced
    complexity = metadata.get('complexity', 'low')
    if any(word in query_lower for word in ['architecture', 'design', 'pattern', 'optimize']):
        if complexity in {'medium', 'high'}:
            boosted_score *= 1.15
    
    # Slightly penalize if too simple for complex queries
    if complexity == 'low' and len(query_lower.split()) > 8:
        boosted_score *= 0.95
    
    return boosted_score


__all__ = [
    'embed_chunks',
    'extract_semantic_metadata',
    'generate_enriched_embedding_text',
    'boost_embedding_score',
]
