import os
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Load environment variables from the .env file in the current directory
load_dotenv()

# 2. Extract configuration tokens safely
SUPABASE_URL = os.getenv("VITE_API_URL") 
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Target the correct key variable

# Fallback parser if your VITE_API_URL points to your frontend/railway domain instead of the database REST route
if not SUPABASE_URL or "railway" in SUPABASE_URL or "vercel" in SUPABASE_URL:
    SUPABASE_URL = "https://sqthzxcbdukmpieeuzly.supabase.co"

# 3. Explicit Validation check
if not SUPABASE_KEY:
    raise ValueError(
        "Missing 'SUPABASE_SERVICE_ROLE_KEY' in your .env file.\n"
        "Please open your .env file and add your key assignment."
    )

print(f"Connecting to Supabase project at: {SUPABASE_URL}...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def populate_parameters():
    print("Fetching leaf nodes from curriculum tree...")
    
    try:
        # Requesting your 340 IITJEE leaf nodes
        response = supabase.table("curriculum_tree") \
            .select("id, title, content_type") \
            .eq("exam_type", "IITJEE") \
            .eq("level", 3) \
            .execute()
            
        nodes = response.data
        print(f"\n🚀 Success! Successfully authenticated and retrieved {len(nodes)} leaf nodes.")
        
        # Iteration sample for viewing structural output data stream
        for node in nodes[:5]: # Prints first 5 rows to confirm it works
            print(f" -> Found Node ID: {node['id']} | [{node['content_type'].upper()}] - {node['title']}")
            
        print("\nReady for parameter generation routines.")
        
    except Exception as e:
        print(f"\nAn error occurred during database operation:\n{str(e)}")

if __name__ == "__main__":
    populate_parameters()