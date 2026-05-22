import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("System cloud credentials mapping configurations missing from environment parameters matrix.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def determine_curriculum_weightage(unit_number: int) -> str:
    """ Matches target core weight categories using designated physics block arrays """
    if unit_number in [11, 12, 13, 14, 16, 18]:
        return "High"
    elif unit_number in [2, 3, 4, 5, 6, 10, 15, 17]:
        return "Medium"
    else:
        return "Low"

def seed_prompt_parameters_matrix():
    print("🛰️ Starting parameter sync ingestion process across system nodes...")
    
    # 1. Capture all topic-level node definitions tracking inside curriculum tree
    try:
        topics_res = supabase.table("curriculum_tree")\
            .select("id, title, unit, exam_type, unit_number")\
            .eq("exam_type", "IITJEE")\
            .eq("level", 2)\
            .eq("subject_id", "4ae2ad11-6a55-484e-8050-5b27668c7606")\
            .execute()
    except Exception as lookup_err:
        print(f"❌ Failed to reach curriculum tree mapping arrays: {lookup_err}")
        return

    topics = topics_res.data or []
    print(f"📦 Identified {len(topics)} master structural topic tracks inside database schema.")

    for idx, t in enumerate(topics, 1):
        topic_title = t.get("title")
        unit_title = t.get("unit")
        unit_num = t.get("unit_number") or 1
        
        print(f"[{idx}/{len(topics)}] Processing metadata for: '{topic_title}' | Unit {unit_num}")

        # 2. Extract grounded payload configurations for this specific topic string context match
        key_formulae_list = []
        common_mistakes_list = []
        inferred_difficulty = "Medium"

        try:
            content_res = supabase.table("generated_content")\
                .select("content, content_type, difficulty")\
                .eq("topic", topic_title)\
                .execute()
            
            content_rows = content_res.data or []
            for row in content_rows:
                c_type = row.get("content_type")
                txt = row.get("content", "").strip()
                
                if row.get("difficulty"):
                    inferred_difficulty = row.get("difficulty")

                if c_type == "formulae" and txt:
                    # Clean the formula rows for insertion
                    lines = [line.strip("- *• \t") for line in txt.split("\n") if line.strip()]
                    key_formulae_list.extend(lines[:8]) # Cap elements parameter threshold
                elif c_type == "common_mistakes" and txt:
                    lines = [line.strip("- *• \t") for line in txt.split("\n") if line.strip()]
                    common_mistakes_list.extend(lines[:5])
        except Exception as content_err:
            print(f"   ⚠️ Content collection skipped on topic match step: {content_err}")

        weight = determine_curriculum_weightage(unit_num)

        # 3. Locate the 4 downstream leaf child nodes mapped to this parent topic row component
        try:
            leaves_res = supabase.table("curriculum_tree")\
                .select("id, content_type, prompt_template_id")\
                .eq("parent_id", t.get("id"))\
                .eq("is_leaf", True)\
                .execute()
            
            leaf_nodes = leaves_res.data or []
            
            for leaf in leaf_nodes:
                leaf_id = leaf.get("id")
                c_type = leaf.get("content_type")
                template_id = leaf.get("prompt_template_id")

                if not template_id:
                    # Defensive fallback: resolve active matching templates out of relation lookup values
                    tpl_res = supabase.table("prompt_templates")\
                        .select("id")\
                        .eq("content_type", "concept" if c_type == "concept" else c_type)\
                        .eq("exam_subject_id", "4ae2ad11-6a55-484e-8050-5b27668c7606")\
                        .eq("is_active", True)\
                        .maybe_single()\
                        .execute()
                    if tpl_res and tpl_res.data:
                        template_id = tpl_res.data.get("id")

                if not template_id:
                    print(f"   ❌ Missing template references for node category context track: {c_type}")
                    continue

                # 4. Perform transaction upsert seeding prompt parameter allocations safely
                supabase.table("prompt_parameters").upsert({
                    "curriculum_tree_id": str(leaf_id),
                    "prompt_template_id": str(template_id),
                    "topic": topic_title,
                    "unit": unit_title,
                    "exam_type": "IITJEE",
                    "subject": "Physics",
                    "difficulty": inferred_difficulty,
                    "weightage": weight,
                    "key_formulae": key_formulae_list,
                    "prerequisites": ["Basic Trigonometry Foundations", "Vector Resolution Frameworks"] if unit_num > 2 else [],
                    "common_mistakes": common_mistakes_list if common_mistakes_list else ["Misapplying dimensional homogeneity across logarithmic power expansions."],
                    "top_k_theory": 3,
                    "top_k_examples": 3,
                    "top_k_questions": 4,
                    "similarity_threshold": 0.25
                }, on_conflict="curriculum_tree_id").execute()

        except Exception as leaf_err:
            print(f"   ❌ Failed updating prompt child leaves records sequence context: {leaf_err}")

    print("🏁 Pipeline processing structural database synchronization has successfully completed execution.")

if __name__ == "__main__":
    seed_prompt_parameters_matrix()