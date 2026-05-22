# =====================================================================
# DYNAMIC HIERARCHICAL RECURSIVE SYLLABUS TREE ENDPOINT (IIT-JEE / NEET)
# =====================================================================

@router.get("/exam/{exam_id}/tree")
def get_hierarchical_curriculum_tree(
    exam_id: str, 
    subject_id: Optional[str] = Query(None), 
    db: Session = Depends(get_db)
):
    """
    Fetches flat curriculum nodes for a target exam and packs them recursively 
    into an integrated nested multi-pane tree layout array: 
    Units (Level 1) -> Topics (Level 2) -> Leaves (Level 3 Workspaces).
    """
    # 1. Pull the data from curriculum_tree using clean raw SQL to bypass ORM entity bloat
    sql_query = """
        SELECT id, parent_id, title, level, unit_number, display_order, is_leaf, content_type
        FROM public.curriculum_tree
        WHERE exam_id = :exam_id
    """
    params = {"exam_id": exam_id}
    
    # Optional parameter filter if your frontend restricts workspace by subject panel selection
    if subject_id:
        sql_query += " AND subject_id = :subject_id"
        params["subject_id"] = subject_id
        
    sql_query += " ORDER BY level ASC, unit_number ASC, display_order ASC"
    
    try:
        result = db.execute(text(sql_query), params)
        all_nodes = [dict(row) for row in result.mappings()]
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database execution failed on structural tree compilation: {str(e)}"
        )

    if not all_nodes:
        # Graceful return to avoid UI component crashes if the database table is clean empty
        return []

    # 2. Build indexed lookup map matrices
    nodes_by_id = {}
    for node in all_nodes:
        # Ensure primitive UUID string serialization to maintain clean JSON compliance
        node_id = str(node["id"])
        nodes_by_id[node_id] = {
            "id": node_id,
            "parent_id": str(node["parent_id"]) if node["parent_id"] else None,
            "title": node["title"],
            "level": node["level"],
            "unit_number": node["unit_number"],
            "is_leaf": node["is_leaf"],
            "content_type": node["content_type"],
            "children": [] # Dynamic branch nesting payload hook
        }

    # 3. Assemble components recursively into a clean hierarchical dictionary array
    root_nodes = []
    for n_id, node in nodes_by_id.items():
        p_id = node["parent_id"]
        if p_id is None or p_id not in nodes_by_id:
            # Level 1 Node: High-level Course Unit Header
            root_nodes.append(node)
        else:
            # Nested Node: Level 2 Topic folders or Level 3 Content leaf workspaces
            parent = nodes_by_id[p_id]
            parent["children"].append(node)

    return root_nodes