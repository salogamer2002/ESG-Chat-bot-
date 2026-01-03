import chainlit as cl
from app.rag_chain import load_rag_chain, load_gap_analysis_chain
import os
from collections import defaultdict
from typing import Dict, Optional
import json
from datetime import datetime
from app.user_db import user_exists, save_user, get_user, list_users, init_db, force_insert_test_user
from urllib.parse import quote
import re

MAX_CHARS = 2000

def split_text(text, max_chars=MAX_CHARS):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def log_conversation(query: str, response: str, sources: list, user_name: str, email: str):
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    log_entry = {
        "timestamp": now.isoformat(),
        "user_name": user_name,
        "user_email": email,
        "query": query,
        "response": response,
        "sources": sources
    }

    os.makedirs("logs", exist_ok=True)
    log_file = os.path.join("logs", f"conversations_{date_str}.jsonl")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
    print("=" * 50)
    print("OAuth callback triggered")
    print(f"Provider: {provider_id}")
    
    # Extract user data
    display_name = raw_user_data.get("name") or (default_user.display_name if default_user else "")
    email = raw_user_data.get("email") or (default_user.identifier if default_user else "")
    organization = raw_user_data.get("organization", "")
    country = raw_user_data.get("location", "")

    if not email:
        print("ERROR: No email found in OAuth data!")
        return None

    # Initialize database
    init_db()
    
    # Check if user exists
    profile_exists = user_exists(email)
    print(f"Profile exists for {email}: {profile_exists}")

    # Create user
    user = cl.User(
        identifier=email,
        display_name=display_name,
        metadata={
            "organization": organization,
            "country": country,
            "profile_completed": profile_exists,
            "provider": provider_id
        },
    )
    
    print(f"Created user: {user.identifier}")
    return user

@cl.on_chat_resume
async def on_chat_resume(thread: cl.types.ThreadDict):
    cl.user_session.set("chat_history", [])
    cl.user_session.set("rag_chain", load_rag_chain())
    cl.user_session.set("gap_chain", load_gap_analysis_chain())

    # Load previous conversation history if it exists
    conversation_history = cl.user_session.get("conversation_history", [])
    
    for message in thread["steps"]:
        if message["type"] == "user_message":
            conversation_history.append(f"User: {message['output']}")
            cl.user_session.get("chat_history").append({"role": "user", "content": message["output"]})
        elif message["type"] == "assistant_message":
            conversation_history.append(f"Assistant: {message['output']}")
            cl.user_session.get("chat_history").append({"role": "assistant", "content": message["output"]})
    cl.user_session.set("conversation_history", conversation_history)

@cl.on_chat_start
async def on_chat_start():
    print("=" * 50)
    print("🚀 on_chat_start - BEGIN")
    
    # Force initialize database and insert test user
    print("🛠️  Forcing database initialization...")
    force_insert_test_user()
    
    app_user = cl.user_session.get("user")
    
    if not app_user or not app_user.identifier:
        await cl.Message(content="❌ Please log in with Google.").send()
        return
    
    user_email = app_user.identifier.lower().strip()
    print(f"👤 User email: {user_email}")
    
    # Initialize chains with AI enabled
    cl.user_session.set("chat_history", [])
    cl.user_session.set("conversation_history", [])
    cl.user_session.set("rag_chain", load_rag_chain(use_ai=True))  # ✅ AI enabled
    cl.user_session.set("gap_chain", load_gap_analysis_chain(use_ai=True))

    # Check profile
    profile_exists = user_exists(user_email)
    print(f"🔍 Profile exists for '{user_email}': {profile_exists}")
    
    # List all users for debugging
    all_users = list_users()
    print(f"👥 Users in database ({len(all_users)}):")
    for user in all_users:
        print(f"   - {user[0]}")
    
    if not profile_exists:
        # Force insert user
        print("🔄 User not found, forcing insert...")
        success = save_user(
            email=user_email,
            name=app_user.display_name,
            use_case="Academic",
            organization="Auto-Inserted",
            industry="Technology",
            sector="Software",
            country="Pakistan",
            consent=True
        )
        
        if success:
            print("✅ User auto-inserted successfully!")
            profile_exists = True
        else:
            print("❌ Failed to auto-insert user")
    
    if not profile_exists:
        # Show profile completion link
        base_url = os.getenv('URL', 'http://localhost:8000').rstrip('/')
        profile_url = f"{base_url}/profile?email={quote(user_email)}&name={quote(app_user.display_name)}"
        
        await cl.Message(
            content=f"""🚧 **Profile Setup Required**

Hi **{app_user.display_name}**!

Please complete your profile to get started:
👉 [Complete Profile]({profile_url})

After completing, return here and type **"done"**
"""
        ).send()
        
        cl.user_session.set("profile_incomplete", True)
        cl.user_session.set("waiting_for_profile_completion", True)
        return
    
    # Profile exists - welcome message
    cl.user_session.set("profile_incomplete", False)
    cl.user_session.set("waiting_for_profile_completion", False)
    
    user_details = get_user(user_email)
    org_name = user_details.get("organization", "your organization") if user_details else "your organization"
    
    await cl.Message(
        content=f"""✅ **Welcome back, {app_user.display_name}!**

Your profile for **{org_name}** is ready.

**🤖 I'm your ESG Compliance Assistant powered by Fireworks AI**

**How can I help you today?**
- Ask about ESG regulations (ESRS, GRI, CSRD, SASB)
- Upload documents for compliance review
- Get implementation guidance
- Compare different frameworks

**Try:** *"What are the key ESRS disclosure requirements?"*
"""
    ).send()
    
    print("🎯 on_chat_start - END")
    print("=" * 50)


@cl.on_message
async def on_message(message: cl.Message):
    user = cl.user_session.get("user")
    
    # Handle profile completion flow
    if cl.user_session.get("waiting_for_profile_completion", False):
        user_msg = message.content.strip().lower()
        
        if user_msg in ["done", "refresh", "ready", "go", "start"]:
            # Check if profile now exists
            if user and user.identifier:
                email = user.identifier.lower().strip()
                exists = user_exists(email)
                
                if not exists:
                    # Auto-create profile
                    save_user(
                        email=email,
                        name=user.display_name,
                        use_case="Academic",
                        organization="Auto-Created",
                        industry="Technology",
                        sector="Software",
                        country="Unknown",
                        consent=True
                    )
                    exists = True
                
                if exists:
                    cl.user_session.set("profile_incomplete", False)
                    cl.user_session.set("waiting_for_profile_completion", False)
                    
                    await cl.Message(
                        content="✅ **Profile verified! Welcome to ESG Compliance Chatbot.**"
                    ).send()
                    
                    await cl.Message(
                        content="**Quick start:**\n• Ask about ESG regulations\n• Upload documents\n• Get compliance help\n\n**Try:** *What is CSRD?*"
                    ).send()
                    return
            
            await cl.Message(
                content="🔄 Checking profile... Please complete profile form and try 'done' again."
            ).send()
            return
        else:
            await cl.Message(
                content="Type **'done'** after completing your profile"
            ).send()
            return
    
    # Handle normal messages
    chat_history = cl.user_session.get("chat_history")
    conversation_history = cl.user_session.get("conversation_history", [])
    qa = cl.user_session.get("rag_chain")
    gap_chain = cl.user_session.get("gap_chain")
    
    if qa is None:
        qa = load_rag_chain(use_ai=True)
        cl.user_session.set("rag_chain", qa)
    
    if gap_chain is None:
        gap_chain = load_gap_analysis_chain(use_ai=True)
        cl.user_session.set("gap_chain", gap_chain)

    # Handle file uploads
    if message.elements:
        for element in message.elements:
            if element.type == "file":
                file_path = element.path
                file_name = element.name
                await cl.Message(content=f"📄 Received file: `{file_name}`. Analyzing...").send()

                from app.file_analysis import analyze_document_for_compliance
                result = await analyze_document_for_compliance(file_path, gap_chain)
                await cl.Message(content=result).send()
                return

    conversation_history.append(f"User: {message.content}")
    chat_history.append({"role": "user", "content": message.content})

    try:
        print(f"🔍 Processing query: {message.content}")
        
        # Get response from RAG chain
        if hasattr(qa, 'invoke'):
            result = qa.invoke(message.content)
        else:
            result = qa(message.content)
        
        print(f"✅ Got result from RAG chain")
        
        # Extract answer
        if isinstance(result, dict):
            answer = result.get("result", "")
            sources = result.get("source_documents", [])
        else:
            answer = str(result)
            sources = []
        
        # Clean up response
        pattern = r"(?:\*\*why this is correct\*\*|why this is correct):?"
        answer = re.sub(pattern, " ", answer, flags=re.IGNORECASE)

        pattern = r"(?:\*\*follow-up questions\*\*|follow-up questions):?"
        answer = re.sub(pattern, " ", answer, flags=re.IGNORECASE)

        chat_history.append({"role": "assistant", "content": answer})
        conversation_history.append(f"Assistant: {answer}")

        # Send response (no "limited sources" message for AI responses)
        await cl.Message(content=answer.strip()).send()

        # Log conversation
        if user:
            log_conversation(
                query=message.content,
                response=answer.strip(),
                sources=[getattr(s, 'metadata', {}).get("source", "") for s in sources],
                user_name=user.display_name,
                email=user.identifier
            )

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        import traceback
        traceback.print_exc()
        await cl.Message(content=f"❌ Sorry, I encountered an error. Please try again or rephrase your question.").send()