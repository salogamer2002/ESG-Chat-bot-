import os
from fastapi import FastAPI, Request, Form, HTTPException, APIRouter
from fastapi.staticfiles import StaticFiles
from chainlit.server import app as chainlit_app
from dotenv import load_dotenv
from app.user_db import save_user, user_exists, init_db, list_users
from fastapi.responses import HTMLResponse
import jwt
from typing import Dict, Any

load_dotenv()
init_db()

router = APIRouter(prefix="/api")

CHAINLIT_AUTH_SECRET = os.getenv("CHAINLIT_AUTH_SECRET")
JWT_ALGO = "HS256"

SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Profile Submitted Successfully</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
    </style>
</head>
<body class="flex items-center justify-center min-h-screen bg-gray-50 px-4">
    <div class="bg-white rounded-2xl shadow-md w-full max-w-md p-8 border border-gray-200 text-center">
        <div class="flex flex-col items-center mb-6">
            <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            <h2 class="text-2xl font-semibold text-gray-800">Profile Submitted Successfully!</h2>
            <p class="text-gray-600 mt-2">Your information has been saved. You can now return to the chat.</p>
        </div>
        
        <div class="space-y-4">
            <p class="text-sm text-gray-500">Return to the chat window and type <span class="font-mono bg-gray-100 px-2 py-1 rounded">done</span> to start using the ESG Compliance Chatbot.</p>
            
            <button onclick="window.close()" 
                    class="w-full bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-lg shadow-md transition-colors font-medium">
                Close Window & Return to Chat
            </button>
            
            <p class="text-xs text-gray-400 mt-4">This window will close automatically in 10 seconds...</p>
        </div>
    </div>
    
    <script>
        // Auto-close after 10 seconds
        setTimeout(() => {
            window.close();
        }, 10000);
        
        // Try to send message to parent window if opened from popup
        window.onload = function() {
            try {
                window.opener.postMessage({ type: 'profile_completed', status: 'success' }, '*');
            } catch (e) {
                console.log('Could not notify parent window:', e);
            }
        };
    </script>
</body>
</html>
"""

app = FastAPI()

# Mount directories
DOCUMENTS_PATH = os.path.abspath("data/raw_docs")
if os.path.exists(DOCUMENTS_PATH):
    app.mount("/docs", StaticFiles(directory=DOCUMENTS_PATH), name="docs")

PUBLIC_PATH = os.path.abspath("public")
if os.path.exists(PUBLIC_PATH):
    app.mount("/public", StaticFiles(directory=PUBLIC_PATH), name="public")

@app.get("/profile", response_class=HTMLResponse)
async def profile_form(request: Request):
    email = request.query_params.get("email", "")
    name = request.query_params.get("name", "")
    organization = request.query_params.get("organization", "")
    country = request.query_params.get("country", "")

    # Read the HTML file
    html_path = os.path.join(PUBLIC_PATH, "profile_form.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        # Fallback HTML if file doesn't exist
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Complete Your Profile | Mizan AI</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        </head>
        <body class="flex items-center justify-center min-h-screen bg-gray-50 px-4">
            <div class="bg-white rounded-2xl shadow-md w-full max-w-md p-8">
                <h1 class="text-2xl font-bold text-gray-800 mb-2">Complete Your Profile</h1>
                <p class="text-gray-600 mb-6">Please complete your profile to continue using Mizan AI.</p>
                
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                    <p class="text-yellow-800 text-sm">
                        <span class="font-semibold">Note:</span> This page requires authentication. 
                        Please log in through the chat interface first.
                    </p>
                </div>
                
                <a href="/" 
                   class="inline-flex items-center justify-center w-full bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-lg shadow transition-colors">
                    Return to Chat
                </a>
            </div>
        </body>
        </html>
        """
    
    return HTMLResponse(content=html)

@app.post("/submit_profile")
async def submit_profile(
    email: str = Form(...),
    name: str = Form(...),
    use_case: str = Form(...),
    organization: str = Form(...),
    industry: str = Form(...),
    sector: str = Form(...),
    country: str = Form(...),
    consent: bool = Form(False)
):
    """Handle profile submission"""
    print(f"📝 Profile submission received for: {email}")
    print(f"   Name: {name}")
    print(f"   Organization: {organization}")
    print(f"   Consent: {consent}")
    
    # Validate required fields
    if not consent:
        raise HTTPException(status_code=400, detail="You must agree to the consent")
    
    required_fields = {
        "name": name,
        "use_case": use_case,
        "organization": organization,
        "industry": industry,
        "sector": sector,
        "country": country
    }
    
    missing = [k for k, v in required_fields.items() if not v.strip()]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing)}"
        )
    
    try:
        # Save user to database
        success = save_user(
            email=email,
            name=name,
            use_case=use_case,
            organization=organization,
            industry=industry,
            sector=sector,
            country=country,
            consent=consent
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save profile")
        
        # List all users for debugging
        print("👥 Current users in database:")
        users = list_users()
        for user in users:
            print(f"   - {user[0]} ({user[1]})")
        
        # Verify save
        if not user_exists(email):
            raise HTTPException(status_code=500, detail="Profile not saved correctly")
        
        print(f"✅ Profile saved successfully for: {email}")
        return HTMLResponse(content=SUCCESS_HTML)
        
    except Exception as e:
        print(f"❌ Error saving profile: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/simple-profile", response_class=HTMLResponse)
async def simple_profile_form():
    """Simple working profile form"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Complete Your Profile - Simple Form</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <script>
            function submitForm() {
                // Validate all fields
                const required = ['name', 'use_case', 'organization', 'industry', 'sector', 'country'];
                let missing = false;
                
                required.forEach(id => {
                    const field = document.getElementById(id);
                    if (!field.value.trim()) {
                        field.style.borderColor = 'red';
                        missing = true;
                    } else {
                        field.style.borderColor = '';
                    }
                });
                
                if (missing) {
                    alert('Please fill all required fields marked with *');
                    return false;
                }
                
                // Show loading
                const btn = document.getElementById('submitBtn');
                btn.innerHTML = 'Submitting...';
                btn.disabled = true;
                return true;
            }
        </script>
    </head>
    <body class="bg-gray-50 min-h-screen p-4">
        <div class="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md mt-8">
            <h1 class="text-2xl font-bold text-center mb-6">Complete Your Profile</h1>
            
            <form action="/submit_profile" method="POST" onsubmit="return submitForm()" class="space-y-4">
                <!-- Hidden email field -->
                <input type="hidden" name="email" id="email" value="salman.tayyab.kamran@gmail.com">
                
                <div>
                    <label class="block font-medium mb-1">Full Name *</label>
                    <input type="text" name="name" id="name" 
                           value="Muhammad Salman"
                           required class="w-full p-2 border rounded">
                </div>
                
                <div>
                    <label class="block font-medium mb-1">Use Case *</label>
                    <select name="use_case" id="use_case" required class="w-full p-2 border rounded">
                        <option value="">Select...</option>
                        <option value="Academic" selected>Academic</option>
                        <option value="Official">Official</option>
                        <option value="Research">Research</option>
                        <option value="General Curiosity">General Curiosity</option>
                    </select>
                </div>
                
                <div>
                    <label class="block font-medium mb-1">Organization *</label>
                    <input type="text" name="organization" id="organization"
                           value="University" 
                           required class="w-full p-2 border rounded">
                </div>
                
                <div>
                    <label class="block font-medium mb-1">Industry *</label>
                    <select name="industry" id="industry" required class="w-full p-2 border rounded">
                        <option value="">Select...</option>
                        <option value="Education" selected>Education</option>
                        <option value="Technology">Technology</option>
                        <option value="Finance">Finance</option>
                        <option value="Healthcare">Healthcare</option>
                        <option value="Government">Government</option>
                    </select>
                </div>
                
                <div>
                    <label class="block font-medium mb-1">Sector *</label>
                    <input type="text" name="sector" id="sector"
                           value="Higher Education" 
                           required class="w-full p-2 border rounded">
                </div>
                
                <div>
                    <label class="block font-medium mb-1">Country *</label>
                    <select name="country" id="country" required class="w-full p-2 border rounded">
                        <option value="">Select...</option>
                        <option value="Pakistan" selected>Pakistan</option>
                        <option value="USA">USA</option>
                        <option value="UK">UK</option>
                        <option value="Canada">Canada</option>
                        <option value="Germany">Germany</option>
                    </select>
                </div>
                
                <div class="flex items-center">
                    <input type="checkbox" name="consent" id="consent" required class="mr-2">
                    <label for="consent">I consent to store this information *</label>
                </div>
                
                <button type="submit" id="submitBtn" 
                        class="w-full bg-green-600 text-white p-3 rounded font-medium hover:bg-green-700">
                    Submit & Start Chatting
                </button>
            </form>
            
            <div class="mt-6 p-4 bg-blue-50 rounded">
                <h3 class="font-bold mb-2">Instructions:</h3>
                <ol class="list-decimal pl-5 space-y-1 text-sm">
                    <li>Click "Submit & Start Chatting"</li>
                    <li>Wait for success confirmation</li>
                    <li>Return to chat window</li>
                    <li>Type <strong>"done"</strong></li>
                </ol>
                <div class="mt-3 p-2 bg-gray-100 rounded">
                    <p class="text-sm"><strong>Debug:</strong> Email is pre-filled as: <code>salman.tayyab.kamran@gmail.com</code></p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

def _pick_token(request: Request) -> str | None:
    # 1) Authorization header
    auth = request.headers.get("authorization")
    if auth and auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    # 2) Common cookie names
    for key in ("chainlit-jwt", "access_token", "token", "Authorization"):
        if key in request.cookies:
            return request.cookies[key]
    # 3) Fallback: first JWT-looking cookie
    for v in request.cookies.values():
        if v.count(".") == 2:
            return v
    return None

def _decode_chainlit_jwt(token: str) -> Dict[str, Any]:
    if not CHAINLIT_AUTH_SECRET:
        raise HTTPException(status_code=500, detail="Server misconfigured: CHAINLIT_AUTH_SECRET missing")
    try:
        return jwt.decode(token, CHAINLIT_AUTH_SECRET, algorithms=[JWT_ALGO])
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid auth token: {e}")

@router.get("/profile-status")
def profile_status(request: Request):
    if not CHAINLIT_AUTH_SECRET:
        raise HTTPException(500, "CHAINLIT_AUTH_SECRET missing")

    token = _pick_token(request)
    if not token:
        raise HTTPException(401, "No auth token found")

    try:
        claims: Dict[str, Any] = jwt.decode(token, CHAINLIT_AUTH_SECRET, algorithms=[JWT_ALGO])
    except Exception as e:
        raise HTTPException(401, f"Invalid token: {e}")

    email = claims.get("identifier") or claims.get("email") or claims.get("sub")
    name = claims.get("display_name") or claims.get("name") or ""
    if not email:
        raise HTTPException(400, "Token missing user identifier")

    return {"exists": bool(user_exists(email)), "email": email, "name": name}

app.include_router(router)
# Mount Chainlit's app under root
app.mount("/", chainlit_app)