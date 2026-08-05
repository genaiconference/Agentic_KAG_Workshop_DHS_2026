import ast
import pandas as pd
from IPython.display import display, Markdown


def _parse_content(content):
    """Best-effort conversion of an item's `content` into a dict."""
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        try:
            parsed = ast.literal_eval(content)
            if isinstance(parsed, dict):
                return parsed
            return {"content": parsed}
        except (ValueError, SyntaxError):
            return {"content": content}
    return {"content": content}


def pretty_retriever_results(result, title=None, top_k=None):
    """Pretty-print results from ANY neo4j-graphrag retriever as a DataFrame.

    Works with:
      - `.get_search_results(...)` output  -> uses `.records` (neo4j.Record)
      - `.search(...)` output              -> uses `.items` (RetrieverResultItem)

    Returns the pandas DataFrame so it can be reused downstream.
    """
    rows = []

    # Case 1: get_search_results(...) -> RawSearchResult with `.records`
    if hasattr(result, "records"):
        for rec in result.records:
            row = dict(rec)  # neo4j.Record -> dict
            node = row.pop("node", None)
            if node is not None:
                row = {**dict(node), **row}
            rows.append(row)

    # Case 2: search(...) -> RetrieverResult with `.items`
    elif hasattr(result, "items"):
        for item in result.items:
            row = _parse_content(getattr(item, "content", item))
            meta = getattr(item, "metadata", None) or {}
            if "score" in meta and "score" not in row:
                row["score"] = meta["score"]
            rows.append(row)
    else:
        rows = [dict(r) for r in result]

    df = pd.DataFrame(rows)

    # Move score to the end and round it for readability
    if "score" in df.columns:
        df["score"] = pd.to_numeric(df["score"], errors="coerce").round(4)
        df = df[[c for c in df.columns if c != "score"] + ["score"]]

    if top_k is not None:
        df = df.head(top_k)

    if title:
        display(Markdown(f"#### {title}  &nbsp;·&nbsp; _{len(df)} result(s)_"))

    # Show any generated Cypher (Text2Cypher) if present
    meta = getattr(result, "metadata", None) or {}
    if isinstance(meta, dict) and meta.get("cypher"):
        display(Markdown(f"**Generated Cypher**\n```cypher\n{meta['cypher']}\n```"))

    display(df)
