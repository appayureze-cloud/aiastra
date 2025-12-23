"""
Simple frontend routes for Auth0 login testing
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import os

frontend_router = APIRouter(tags=["frontend"])

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")

@frontend_router.get("/login-page", response_class=HTMLResponse)
async def login_page():
    """Simple login page for testing Auth0 integration"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Astra - Ayurvedic Wellness Assistant</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 400px;
                width: 90%;
            }}
            h1 {{
                color: #333;
                margin-bottom: 0.5rem;
                font-size: 2rem;
            }}
            .subtitle {{
                color: #666;
                margin-bottom: 2rem;
                font-size: 1.1rem;
            }}
            .login-btn {{
                background: #4285f4;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 1.1rem;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: background 0.3s;
            }}
            .login-btn:hover {{
                background: #3367d6;
            }}
            .features {{
                margin-top: 2rem;
                text-align: left;
            }}
            .feature {{
                margin: 0.5rem 0;
                color: #555;
            }}
            .namaste {{
                font-size: 1.2rem;
                color: #8B4513;
                margin-bottom: 1rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="namaste">🕉️ Namaste 🕉️</div>
            <h1>Astra</h1>
            <p class="subtitle">Your Ayurvedic Wellness Assistant</p>
            
            <a href="https://{AUTH0_DOMAIN}/authorize?response_type=code&client_id={AUTH0_CLIENT_ID}&redirect_uri=http://localhost:5000/callback&scope=openid%20profile%20email&connection=google-oauth2" 
               class="login-btn">
                🔐 Login with Gmail
            </a>
            
            <div class="features">
                <h3>Features:</h3>
                <div class="feature">✨ Multilingual support (20+ languages)</div>
                <div class="feature">🌿 Personalized Ayurvedic guidance</div>
                <div class="feature">💬 Persistent chat history</div>
                <div class="feature">🧘‍♀️ Holistic wellness recommendations</div>
            </div>
        </div>
        
        <script>
            // Handle Auth0 callback
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');
            
            if (code) {{
                // Show loading message
                document.body.innerHTML = `
                    <div class="container">
                        <h1>Authenticating...</h1>
                        <p>Please wait while we log you in.</p>
                    </div>
                `;
                
                // Exchange code for token (this would typically be done on the backend)
                console.log('Auth code received:', code);
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@frontend_router.get("/callback")
async def auth_callback(request: Request):
    """Handle Auth0 callback"""
    code = request.query_params.get("code")
    if code:
        # In a real app, you would exchange the code for tokens here
        return HTMLResponse(f"""
        <html>
        <body>
            <h1>Authentication Successful!</h1>
            <p>Authorization code: {code}</p>
            <p>You can now use the API with your JWT token.</p>
            <a href="/docs">Go to API Documentation</a>
        </body>
        </html>
        """)
    else:
        return HTMLResponse("""
        <html>
        <body>
            <h1>Authentication Failed</h1>
            <p>No authorization code received.</p>
            <a href="/login-page">Try Again</a>
        </body>
        </html>
        """)