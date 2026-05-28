import asyncio
import sys
from backend.tools.zoho_tools import list_projects

async def main():
    # Provide the user_id that you see in your app.db (from the Phase 2 login)
    user_id = input("Enter the user_id from app.db to test with: ").strip()
    if not user_id:
        print("Please provide a valid user_id to test.")
        sys.exit(1)

    print(f"\nTesting list_projects tool for user '{user_id}'...")
    try:
        # LangChain tools can be invoked via .ainvoke
        result = await list_projects.ainvoke({"user_id": user_id})
        
        print(f"\nSuccess! Found {len(result)} projects:")
        for p in result:
            print(f"- {p.get('project_name')} (ID: {p.get('project_id')})")
            
    except Exception as e:
        print(f"\nAn error occurred while testing the tool:\n{e}")

if __name__ == "__main__":
    asyncio.run(main())
