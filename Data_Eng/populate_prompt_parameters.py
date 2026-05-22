"""
populate_prompt_parameters.py

Populates public.prompt_parameters for all IITJEE Physics topics.
Inserts 4 rows per topic (one per leaf type: concept, solved_problems,
unsolved_problems, concept_test) — 340 rows total for Physics.

Uses Pydantic + Gemini Structured Outputs to guarantee syntax perfection.
Upserts into prompt_parameters — safe to re-run.
"""

import os
import json
import time
import psycopg2
import psycopg2.extras
from uuid import uuid4
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL       = os.environ["DATABASE_DIRECT_URL"]
GEMINI_KEY   = os.environ["GEMINI_API_KEY"]
GEN_MODEL    = "gemini-2.5-flash"   
SUBJECT_ID   = "4ae2ad11-6a55-484e-8050-5b27668c7606"  # IITJEE_PHYSICS
EXAM_TYPE    = "IITJEE"
SUBJECT      = "Physics"
SLEEP_SEC    = 0.5   # Base rate limit buffer

client = genai.Client(api_key=GEMINI_KEY)

# ── UNIT WEIGHTAGE MAP ────────────────────────────────────────
WEIGHTAGE = {
    1:  "Low",     # Units and Measurement
    2:  "Medium",  # Kinematics
    3:  "Medium",  # Laws of Motion
    4:  "Medium",  # Work Energy Power
    5:  "Medium",  # Rotational Motion
    6:  "Medium",  # Gravitation
    7:  "Low",     # Properties of Solids and Liquids
    8:  "Low",     # Thermodynamics
    9:  "Low",     # Kinetic Theory
    10: "Medium",  # Oscillations and Waves
    11: "High",    # Electrostatics
    12: "High",    # Current Electricity
    13: "High",    # Magnetic Effects
    14: "High",    # EM Induction and AC
    15: "Low",     # EM Waves
    16: "High",    # Optics
    17: "Medium",  # Dual Nature
    18: "High",    # Atoms and Nuclei
    19: "Low",     # Electronic Devices
    20: "Low",     # Experimental Skills
}

# ── PYDANTIC OBJECT FOR STRUCTURED OUTPUT VALIDATION ──────────
class PhysicsTopicParameters(BaseModel):
    difficulty: str = Field(description="Must be exactly: Easy or Medium or Hard relative to the IIT JEE testing standard.")
    key_formulae: list[str] = Field(description="A list of 4 to 6 core equations in plain readable text layout. No raw LaTeX or unescaped backslashes.")
    common_mistakes: list[str] = Field(description="A list of exactly 3 granular conceptual errors or calculation traps students fall into on this exact topic.")
    prerequisites: list[str] = Field(description="A list of 2 to 3 foundational physics chapters a student must know first.")

# ── GENERATE PARAMETERS VIA GEMINI ───────────────────────────
def generate_parameters(topic: str, unit: str, unit_number: int, retries: int = 4, backoff: int = 15) -> dict | None:
    """
    Calls Gemini utilizing clean Pydantic schema validation. Handles gRPC network overhead,
    503 load balancing unavailability spikes, and rate limitations with exponential sleep pacing.
    """
    prompt = f"""You are an elite IIT JEE Physics curriculum master designer.

Generate accurate pedagogical metadata configurations for this topic:
Topic: "{topic}"
Unit:  "{unit}"
Exam:  IIT JEE Main and Advanced structural mapping.

Rules:
- difficulty: Evaluate relative to the true JEE landscape.
- key_formulae: Use plain, readable text layouts only. Example: "F = G*m1*m2 / r^2" or "v = u + a*t". Do NOT provide raw backslashes or complex formatting parameters.
- common_mistakes: Outline 3 highly specific engineering errors or calculation mistakes common to this topic.
- prerequisites: Identify 2 to 3 baseline physics concepts needed for context.
"""

    try:
        # Pass the Pydantic class object directly into the content config context block
        response = client.models.generate_content(
            model=GEN_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PhysicsTopicParameters,
                temperature=0.1,  # Lowered variance to enforce strict syntactic adherence
                max_output_tokens=1200,
            )
        )
        # Parse the verified structured schema text response safely
        return json.loads(response.text.strip())

    except Exception as e:
        error_msg = str(e)
        print(f"     ⚠️ Generation delay encountered for '{topic}': {error_msg}")
        
        # Capture 503 overloads, high demand limits, or network request socket issues
        if retries > 0:
            print(f"     ⏳ Connection condition met. Backing off for {backoff}s... ({retries} retries remaining)")
            time.sleep(backoff)
            return generate_parameters(topic, unit, unit_number, retries - 1, backoff * 2)
            
        print(f"     ❌ Critical limit reached. Unable to resolve payload for '{topic}'")
        return None

# ── DATABASE QUERIES ──────────────────────────────────────────
def load_topics(cur) -> list[dict]:
    """Load all topic nodes (level=2) for IITJEE Physics."""
    cur.execute("""
        SELECT id, title, unit_number
        FROM public.curriculum_tree
        WHERE exam_type  = %s
          AND level      = 2
          AND subject_id = %s
        ORDER BY unit_number, display_order
    """, (EXAM_TYPE, SUBJECT_ID))
    return cur.fetchall()

def load_leaf_nodes(cur, topic_id: str) -> list[dict]:
    """Load 4 leaf nodes for a given topic."""
    cur.execute("""
        SELECT ct.id, ct.content_type, ct.title,
               pt.id AS template_id
        FROM public.curriculum_tree ct
        LEFT JOIN public.prompt_templates pt
          ON pt.id = ct.prompt_template_id
        WHERE ct.parent_id = %s
          AND ct.is_leaf   = true
        ORDER BY ct.display_order
    """, (topic_id,))
    return cur.fetchall()

def already_exists(cur, leaf_id: str) -> bool:
    """Check if prompt_parameters row exists for this leaf."""
    cur.execute("""
        SELECT 1 FROM public.prompt_parameters
        WHERE curriculum_tree_id = %s
        LIMIT 1
    """, (leaf_id,))
    return cur.fetchone() is not None

def upsert_parameters(cur, leaf: dict, topic: str, unit: str, unit_number: int, params: dict) -> None:
    """Upsert one prompt_parameters row for a leaf node."""
    weightage = WEIGHTAGE.get(unit_number, "Medium")

    key_formulae = list(params.get("key_formulae", []))
    common_mistakes = list(params.get("common_mistakes", []))
    prerequisites = list(params.get("prerequisites", []))

    cur.execute("""
        INSERT INTO public.prompt_parameters (
            id,
            curriculum_tree_id,
            prompt_template_id,
            topic,
            unit,
            exam_type,
            subject,
            difficulty,
            weightage,
            key_formulae,
            common_mistakes,
            prerequisites,
            top_k_theory,
            top_k_examples,
            top_k_questions,
            similarity_threshold
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (curriculum_tree_id, prompt_template_id)
        DO UPDATE SET
            difficulty           = EXCLUDED.difficulty,
            weightage            = EXCLUDED.weightage,
            key_formulae         = EXCLUDED.key_formulae,
            common_mistakes      = EXCLUDED.common_mistakes,
            prerequisites        = EXCLUDED.prerequisites,
            top_k_theory         = EXCLUDED.top_k_theory,
            top_k_examples       = EXCLUDED.top_k_examples,
            top_k_questions      = EXCLUDED.top_k_questions,
            similarity_threshold = EXCLUDED.similarity_threshold
    """, (
        str(uuid4()),
        leaf["id"],
        leaf["template_id"],
        topic,
        unit,
        EXAM_TYPE,
        SUBJECT,
        params.get("difficulty", "Medium"),
        weightage,
        key_formulae,     
        common_mistakes,  
        prerequisites,    
        3,    # top_k_theory
        3,    # top_k_examples
        4,    # top_k_questions
        0.25  # similarity_threshold
    ))

# ── MAIN RUNNER LOOP ──────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  populate_prompt_parameters.py (AI-Native Pydantic Layer)")
    print(f"  Model   : {GEN_MODEL}")
    print(f"  Target  : public.prompt_parameters")
    print(f"  Subject : IITJEE Physics")
    print(f"{'='*60}\n")

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    topics         = load_topics(cur)
    total_topics   = len(topics)
    inserted       = 0
    skipped        = 0
    failed         = 0

    print(f"  Topics found in pipeline: {total_topics}\n")

    for i, topic_node in enumerate(topics, 1):
        topic_id     = str(topic_node["id"])
        topic_title  = topic_node["title"]
        unit_number  = topic_node["unit_number"] or 0

        leaves = load_leaf_nodes(cur, topic_id)
        if not leaves:
            print(f"  [{i:02d}/{total_topics}] {topic_title} — zero child leaf rows localized")
            continue

        unit_name = f"Unit {unit_number}"

        print(f"  [{i:02d}/{total_topics}] {topic_title}")
        print(f"            {unit_name}")

        # Skip verification rule logic to easily resume crashed or filled tracks
        all_exist = all(already_exists(cur, str(leaf["id"])) for leaf in leaves)
        if all_exist:
            print(f"            ⏭  All 4 parameters localized in database — skipping topic row")
            skipped += 1
            continue

        # Execute validated parameters query
        params = generate_parameters(topic_title, unit_name, unit_number)
        if not params:
            print(f"            ❌ Processing failed after maximum retries — skipping topic")
            failed += 1
            continue

        print(f"            difficulty={params.get('difficulty')} "
              f"weightage={WEIGHTAGE.get(unit_number,'Medium')} "
              f"formulae={len(params.get('key_formulae',[]))}")

        leaf_count = 0
        for leaf in leaves:
            leaf = dict(leaf)
            if not leaf.get("template_id"):
                print(f"            ⚠️  Target parameter prompt_template_id missing on {leaf['content_type']}")
                continue
            try:
                upsert_parameters(cur, leaf, topic_title, unit_name, unit_number, params)
                leaf_count += 1
            except Exception as e:
                print(f"            ❌ Target transactional failure inside tables [{leaf['content_type']}]: {e}")
                conn.rollback()
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                failed += 1
                break  

        conn.commit()
        inserted += leaf_count
        if leaf_count > 0:
            print(f"            ✓  {leaf_count} parameter rows successfully written to storage clusters.")
        time.sleep(SLEEP_SEC)

    cur.close()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  Sync Execution Results Tracking Summary")
    print(f"  ✅ Upserted : {inserted} parameter records managed")
    print(f"  ⏭  Skipped  : {skipped} baseline chapters handled")
    print(f"  ❌ Failed   : {failed} error rows logged")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()