"""
LangSmith Connection Test Script
This script tests your LangSmith configuration and connection.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_environment_variables():
    """Check if required environment variables are set"""
    print_section("1. Checking Environment Variables")
    
    # LangChain SDK uses LANGCHAIN_* prefix, NOT LANGSMITH_*
    required_vars = {
        'LANGCHAIN_API_KEY': 'Your LangSmith API key',
        'LANGCHAIN_TRACING_V2': 'Enable tracing (should be "true")',
    }
    
    optional_vars = {
        'LANGCHAIN_WORKSPACE_ID': 'Required for organization-scoped keys (valid UUID)',
        'LANGCHAIN_PROJECT': 'Project name for organizing traces',
        'LANGCHAIN_ENDPOINT': 'API endpoint (defaults to api.smith.langchain.com)',
        'LANGCHAIN_DISABLE_RUN_COMPRESSION': 'Disable compression if having issues',
    }
    
    all_good = True
    
    # Check required variables
    print("\n📋 Required Variables:")
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Mask API key for security
            if 'API_KEY' in var:
                display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
                print(f"  ✓ {var}: {display_value} ({description})")
            else:
                print(f"  ✓ {var}: {value} ({description})")
        else:
            print(f"  ✗ {var}: NOT SET - {description}")
            all_good = False
    
    # Check optional variables
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if value:
            print(f"  ✓ {var}: {value} ({description})")
        else:
            print(f"  ○ {var}: Not set - {description}")
    
    # Check for deprecated LANGSMITH_ variables and warn
    print("\n⚠️  Checking for deprecated variables:")
    deprecated = []
    for k, v in os.environ.items():
        if k.startswith("LANGSMITH_"):
            deprecated.append((k, v))
    
    if deprecated:
        print("  Found deprecated LANGSMITH_* variables (should be LANGCHAIN_*):")
        for k, v in deprecated:
            if "API_KEY" in k or "<" in v:
                print(f"    • {k} (should be replaced with LANGCHAIN_* equivalent)")
            else:
                print(f"    • {k}={v} (should be replaced with LANGCHAIN_* equivalent)")
    else:
        print("  ✓ No deprecated LANGSMITH_* variables found")
    
    return all_good
    return all_good

def test_langsmith_client():
    """Test LangSmith client connection"""
    print_section("2. Testing LangSmith Client Connection")
    
    try:
        # Properly import langsmith from poetry environment
        import sys
        import importlib.util
        
        # Try standard import first
        try:
            from langsmith import Client
        except ImportError:
            print("\n⚠️  Direct import failed, attempting via importlib...")
            # Fallback: try to find it in site-packages
            import site
            for path in site.getsitepackages() + [site.getusersitepackages()]:
                spec = importlib.util.spec_from_file_location(
                    "langsmith", 
                    f"{path}/langsmith/__init__.py"
                )
                if spec:
                    langsmith = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(langsmith)
                    Client = langsmith.Client
                    break
            else:
                raise ImportError("LangSmith not found in any site-packages")
        
        print("\n✓ LangSmith package imported successfully")
        
        # Create client with explicit API key
        api_key = os.environ.get("LANGCHAIN_API_KEY")
        if not api_key:
            print("  ⚠️ LANGCHAIN_API_KEY not set, client may fail")
        
        client = Client(api_key=api_key) if api_key else Client()
        print("✓ LangSmith client created successfully")
        
        # Try to list sessions instead of projects (sessions endpoint works better)
        print("\n🔍 Testing API connection...")
        sessions = list(client.list_sessions(limit=1))
        print(f"✓ Successfully connected to LangSmith!")
        print(f"✓ Found {len(sessions)} session(s)")
        
        return True
        
    except ImportError as e:
        print(f"\n✗ LangSmith package import error: {e}")
        print("  Run: poetry install (to ensure langsmith is installed)")
        print("  Or:  poetry add langsmith")
        return False
        
    except Exception as e:
        print(f"\n✗ Error connecting to LangSmith:")
        print(f"  {type(e).__name__}: {str(e)}")
        
        # Provide specific guidance based on error
        if "403" in str(e) or "Forbidden" in str(e):
            print("\n💡 Troubleshooting 403 Forbidden Error:")
            print("  1. Verify your API key is correct (copy fresh from LangSmith)")
            print("  2. Regenerate API key at https://smith.langchain.com/settings")
            print("  3. Try setting LANGCHAIN_DISABLE_RUN_COMPRESSION=true")
            print("  4. If using org account, add valid LANGCHAIN_WORKSPACE_ID")
        elif "401" in str(e) or "Unauthorized" in str(e) or "UUID" in str(e):
            print("\n💡 Troubleshooting 401/UUID Error:")
            print("  1. Your LANGCHAIN_WORKSPACE_ID may be invalid")
            print("  2. Get valid UUID from: https://smith.langchain.com/settings")
            print("  3. Or remove LANGCHAIN_WORKSPACE_ID if not needed")
            print("  4. Generate fresh API key with full permissions")
        
        return False

def test_tracing():
    """Test trace logging functionality"""
    print_section("3. Testing Trace Logging")
    
    try:
        from langsmith import traceable
        
        @traceable(run_type="llm")
        def sample_function(text):
            """A simple function to test tracing"""
            return f"Processed: {text}"
        
        print("\n🔍 Running a traced function...")
        result = sample_function("Hello LangSmith!")
        print(f"✓ Function executed: {result}")
        print("✓ Trace should appear in your LangSmith dashboard")
        
        project_name = os.environ.get('LANGSMITH_PROJECT', 'default')
        print(f"\n📊 Check your traces at: https://smith.langchain.com/")
        print(f"   Project: {project_name}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during trace test:")
        print(f"  {type(e).__name__}: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n🚀 LangSmith Configuration Test")
    print("=" * 60)
    
    # Step 1: Check environment variables
    env_check = check_environment_variables()
    
    if not env_check:
        print("\n⚠️  Warning: Some required environment variables are missing")
        print("   The connection test may fail\n")
    
    # Step 2: Test client connection
    client_test = test_langsmith_client()
    
    # Step 3: Test tracing (only if client connection works)
    trace_test = False
    if client_test:
        trace_test = test_tracing()
    
    # Final summary
    print_section("Summary")
    print(f"\n  Environment Variables: {'✓ Pass' if env_check else '✗ Fail'}")
    print(f"  Client Connection:     {'✓ Pass' if client_test else '✗ Fail'}")
    print(f"  Trace Logging:         {'✓ Pass' if trace_test else '✗ Fail'}")
    
    if client_test and trace_test:
        print("\n✅ All tests passed! Your LangSmith integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        print("\n📖 Helpful Resources:")
        print("  • LangSmith Docs: https://docs.langchain.com/langsmith")
        print("  • API Keys: https://smith.langchain.com/settings")
        print("  • Support: https://support.langchain.com")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()