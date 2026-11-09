"""Request-context parameter resolution for tools."""
import logging

from fastmcp import Context

logger = logging.getLogger(__name__)


def _resolve_context_params(ctx: Context, space_key: str, page_title: str = None) -> tuple:
    """Resolve parameters from context or function arguments."""
    print(f"DEBUG: Context object type: {type(ctx)}")
    print(f"DEBUG: Context attributes: {dir(ctx)}")
    
    # Initialize with function parameters as default
    actual_space_key = space_key
    actual_page_title = page_title
    
    # Try multiple ways to access context data
    context_data = None
    
    # Method 1: Check if context has direct attributes
    if hasattr(ctx, 'confluence_space_key'):
        actual_space_key = ctx.confluence_space_key
        print(f"DEBUG: Found space_key in direct attr: {actual_space_key}")
    
    if hasattr(ctx, 'confluence_page_title') and page_title is not None:
        actual_page_title = ctx.confluence_page_title
        print(f"DEBUG: Found page_title in direct attr: {actual_page_title}")
    
    # Method 2: Check ctx.meta
    if hasattr(ctx, 'meta') and isinstance(ctx.meta, dict):
        print(f"DEBUG: ctx.meta found: {ctx.meta}")
        if 'confluence_space_key' in ctx.meta:
            actual_space_key = ctx.meta['confluence_space_key']
            print(f"DEBUG: Found space_key in meta: {actual_space_key}")
        if 'confluence_page_title' in ctx.meta and page_title is not None:
            actual_page_title = ctx.meta['confluence_page_title']
            print(f"DEBUG: Found page_title in meta: {actual_page_title}")
    
    # Method 3: Check ctx.context
    if hasattr(ctx, 'context') and isinstance(ctx.context, dict):
        print(f"DEBUG: ctx.context found: {ctx.context}")
        if 'confluence_space_key' in ctx.context:
            actual_space_key = ctx.context['confluence_space_key']
            print(f"DEBUG: Found space_key in context: {actual_space_key}")
        if 'confluence_page_title' in ctx.context and page_title is not None:
            actual_page_title = ctx.context['confluence_page_title']
            print(f"DEBUG: Found page_title in context: {actual_page_title}")
    
    # Method 4: Check if ctx itself is a dict-like object
    if hasattr(ctx, 'get'):
        print("DEBUG: ctx has get method, trying as dict")
        space_from_ctx = ctx.get('confluence_space_key')
        title_from_ctx = ctx.get('confluence_page_title')
        if space_from_ctx:
            actual_space_key = space_from_ctx
            print(f"DEBUG: Found space_key via get(): {actual_space_key}")
        if title_from_ctx and page_title is not None:
            actual_page_title = title_from_ctx
            print(f"DEBUG: Found page_title via get(): {actual_page_title}")
    
    # Method 5: Try accessing as __dict__
    if hasattr(ctx, '__dict__'):
        ctx_dict = ctx.__dict__
        print(f"DEBUG: ctx.__dict__: {ctx_dict}")
        if 'confluence_space_key' in ctx_dict:
            actual_space_key = ctx_dict['confluence_space_key']
            print(f"DEBUG: Found space_key in __dict__: {actual_space_key}")
        if 'confluence_page_title' in ctx_dict and page_title is not None:
            actual_page_title = ctx_dict['confluence_page_title']
            print(f"DEBUG: Found page_title in __dict__: {actual_page_title}")
    
    print(f"DEBUG: Final resolution - space_key: '{space_key}' -> '{actual_space_key}', page_title: '{page_title}' -> '{actual_page_title}'")
    logger.info(f"Parameter resolution - space_key: '{space_key}' -> '{actual_space_key}', page_title: '{page_title}' -> '{actual_page_title}'")
    
    return actual_space_key, actual_page_title
