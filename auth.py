"""
auth.py — Login/signup for ChurnGuard Pro.

Two sign-in paths, both resolving to the same `users` collection (keyed on
email) via db.py:

  1. Email + password  — passwords are hashed with bcrypt before storage,
     never kept or logged in plaintext.
  2. Continue with Google — full OAuth 2.0 authorization-code flow using the
     GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / REDIRECT_URI in st.secrets.

If someone signs up with a password using an email that already has a
Google-only account (or vice versa), the two resolve into a single account
rather than creating a duplicate — see db.create_user_with_password() and
upsert_user() for the exact merge rules.
"""

import os
import re
from typing import Optional

import requests
import streamlit as st
from google_auth_oauthlib.flow import Flow

from db import (
    create_user_with_password,
    ensure_indexes,
    get_user,
    hash_password,
    upsert_user,
    verify_password,
)

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LEN = 8

SESSION_KEYS = [
    "auth_message",
    "auth_error",
    "pw_mode",
    "google_oauth_state",
]


# ── Helpers ──────────────────────────────────────────────────────────────────
def _normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def _is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


def _password_issues(password: str, confirm: str) -> list:
    issues = []
    if len(password) < MIN_PASSWORD_LEN:
        issues.append(f"Password must be at least {MIN_PASSWORD_LEN} characters long.")
    if not re.search(r"[A-Za-z]", password):
        issues.append("Password must contain at least one letter.")
    if not re.search(r"[0-9]", password):
        issues.append("Password must contain at least one number.")
    if password != confirm:
        issues.append("Passwords do not match.")
    return issues


def init_auth():
    if "user" not in st.session_state:
        st.session_state.user = None
    for key in SESSION_KEYS:
        if key not in st.session_state:
            st.session_state[key] = None


def _login_user(user_doc: dict) -> None:
    st.session_state.user = {
        "email": user_doc["email"],
        "name": user_doc.get("name", user_doc.get("email", "")),
        "picture": user_doc.get("picture", ""),
        "tier": user_doc.get("tier", "free"),
        "pred_count": user_doc.get("pred_count", 0),
    }
    for key in SESSION_KEYS:
        st.session_state[key] = None
    st.rerun()


def get_current_user() -> Optional[dict]:
    return st.session_state.get("user")


def logout():
    st.session_state.user = None
    for key in SESSION_KEYS:
        st.session_state.pop(key, None)
    st.rerun()


# ── Google OAuth ─────────────────────────────────────────────────────────────
def _google_config() -> Optional[dict]:
    # .strip() matters here: a stray trailing space/newline pasted into
    # secrets.toml (very easy to do) makes Google reject the client silently
    # with a generic "invalid_client" error that's hard to diagnose otherwise.
    client_id = (st.secrets.get("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID", "")).strip()
    client_secret = (st.secrets.get("GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET", "")).strip()
    redirect_uri = (st.secrets.get("REDIRECT_URI") or os.getenv("REDIRECT_URI", "")).strip().rstrip("/")
    if not client_id or not client_secret or not redirect_uri:
        return None
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }


def _build_flow(cfg: dict) -> Flow:
    client_config = {
        "web": {
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [cfg["redirect_uri"]],
        }
    }
    return Flow.from_client_config(
        client_config, scopes=GOOGLE_SCOPES, redirect_uri=cfg["redirect_uri"]
    )


def _google_auth_url(cfg: dict) -> str:
    flow = _build_flow(cfg)
    auth_url, state = flow.authorization_url(
        access_type="online",
        include_granted_scopes="true",
        prompt="select_account",
    )
    st.session_state.google_oauth_state = state
    return auth_url


def _handle_google_callback(cfg: dict) -> None:
    """If Google just redirected back with ?code=..., complete the login."""
    params = st.query_params
    error = params.get("error")
    code = params.get("code")

    if error:
        st.session_state.auth_error = f"Google sign-in was not completed ({error})."
        st.query_params.clear()
        return

    if not code:
        return

    returned_state = params.get("state")
    expected_state = st.session_state.get("google_oauth_state")
    st.query_params.clear()

    if not expected_state or returned_state != expected_state:
        st.session_state.auth_error = (
            "Google sign-in session expired or is invalid. Please try again."
        )
        return

    user_doc = None
    try:
        flow = _build_flow(cfg)
        flow.fetch_token(code=code)
        access_token = flow.credentials.token

        resp = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        info = resp.json()

        email = _normalize_email(info.get("email", ""))
        email_verified = info.get("email_verified", False) in (True, "true")
        name = info.get("name") or email
        picture = info.get("picture", "")

        if not email or not email_verified:
            st.session_state.auth_error = "Google did not return a verified email address."
            return

        user_doc = upsert_user(email, name, picture)

    except Exception as exc:
        # Note: this except is scoped to the network/parsing work above only —
        # _login_user() (which calls st.rerun()) runs outside this try block
        # so a rerun is never mistaken for an OAuth failure.
        st.session_state.auth_error = f"Google sign-in failed: {exc}"
        return

    _login_user(user_doc)


def _render_google_tab() -> None:
    cfg = _google_config()
    if cfg is None:
        st.warning(
            "Google sign-in isn't configured yet. Set GOOGLE_CLIENT_ID, "
            "GOOGLE_CLIENT_SECRET and REDIRECT_URI in `.streamlit/secrets.toml` "
            "(or as environment variables of the same names)."
        )
        return

    st.markdown(
        "<div class='auth-copy'>Use your Google account to sign in. "
        "If you already have a password account with the same email, "
        "they'll be linked automatically.</div>",
        unsafe_allow_html=True,
    )

    try:
        auth_url = _google_auth_url(cfg)
    except Exception as exc:
        st.error(
            "Couldn't build the Google sign-in link — this is almost always a "
            f"misconfigured client. Details: {exc}"
        )
        auth_url = None

    if auth_url:
        st.markdown(
            f"<a href='{auth_url}' target='_self' class='google-btn'>"
            "<svg width='18' height='18' viewBox='0 0 48 48' style='margin-right:10px;'>"
            "<path fill='#FFC107' d='M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.1 8 3l6-6C34.5 6 29.5 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z'/>"
            "<path fill='#FF3D00' d='M6.3 14.7l6.6 4.8C14.6 15.6 18.9 12 24 12c3.1 0 5.8 1.1 8 3l6-6C34.5 6 29.5 4 24 4c-7.7 0-14.4 4.4-17.7 10.7z'/>"
            "<path fill='#4CAF50' d='M24 44c5.3 0 10.1-2 13.6-5.4l-6.3-5.3C29.3 35 26.8 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.6 5.1C9.5 39.6 16.2 44 24 44z'/>"
            "<path fill='#1976D2' d='M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.2 5.7l6.3 5.3C40.6 36.4 44 30.8 44 24c0-1.3-.1-2.4-.4-3.5z'/>"
            "</svg>Continue with Google</a>",
            unsafe_allow_html=True,
        )

    with st.expander("Google sign-in not working? Check this first"):
        st.markdown(
            "The #1 cause of \"Continue with Google\" failing (Google shows "
            "**Error 400: redirect_uri_mismatch**, or nothing happens after you "
            "approve) is that the redirect URI below doesn't *exactly* match one "
            "of the **Authorized redirect URIs** on your OAuth client in the "
            "[Google Cloud Console](https://console.cloud.google.com/apis/credentials) "
            "— including the `https://` vs `http://`, the exact host, and no "
            "trailing slash.\n\n"
            f"**Redirect URI this app is using:**\n```\n{cfg['redirect_uri']}\n```\n"
            "Also double-check:\n"
            "- Your app's URL in **OAuth consent screen → Authorized domains** is added.\n"
            "- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` in `secrets.toml` are copied "
            "with no extra spaces or line breaks.\n"
            "- If your OAuth consent screen is in **Testing** mode, your Google "
            "account's email must be added under **Test users**, or sign-in will "
            "silently fail for anyone else."
        )


# ── Email + password forms ───────────────────────────────────────────────────
def _render_login_form() -> None:
    with st.form(key="login_form"):
        st.markdown(
            "<div class='auth-title'>Sign in</div>"
            "<div class='auth-copy'>Sign in with the email and password you signed up with.</div>",
            unsafe_allow_html=True,
        )
        email = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        submitted = st.form_submit_button("Sign in")

    if not submitted:
        return

    email = _normalize_email(email)
    if not _is_valid_email(email):
        st.error("Please enter a valid email address.")
        return
    if not password:
        st.error("Please enter your password.")
        return

    existing = get_user(email)
    if existing is None:
        st.error("No account found for this email. Please create an account first.")
        return
    if not existing.get("password_hash"):
        st.error(
            "This email is registered via Google sign-in. "
            "Please use 'Continue with Google' to sign in."
        )
        return

    user_doc = verify_password(email, password)
    if user_doc is None:
        st.error("Incorrect email or password.")
        return

    _login_user(user_doc)


def _render_signup_form() -> None:
    with st.form(key="signup_form"):
        st.markdown(
            "<div class='auth-title'>Create an account</div>"
            "<div class='auth-copy'>Sign up with an email and password.</div>",
            unsafe_allow_html=True,
        )
        name = st.text_input("Display name", placeholder="Your full name", key="signup_name")
        email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm = st.text_input("Confirm password", type="password", key="signup_confirm")
        st.markdown(
            "<div class='auth-note'>Use at least 8 characters, with letters and numbers.</div>",
            unsafe_allow_html=True,
        )
        submitted = st.form_submit_button("Create account")

    if not submitted:
        return

    email = _normalize_email(email)
    if not name.strip():
        st.error("Please enter a display name.")
        return
    if not _is_valid_email(email):
        st.error("Please enter a valid email address.")
        return

    issues = _password_issues(password, confirm)
    if issues:
        st.error(" ".join(issues))
        return

    pw_hash = hash_password(password)
    user_doc = create_user_with_password(email, name.strip(), pw_hash)
    if user_doc is None:
        st.error("An account with a password already exists for this email. Please sign in instead.")
        return

    _login_user(user_doc)


# ── Page ─────────────────────────────────────────────────────────────────────
def _render_page_header():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Outfit:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap');
    html,body,[class*="css"]{font-family:'Outfit',sans-serif;color:#e2e0f0;}
    .stApp{
        background:
            radial-gradient(900px 500px at 15% -10%, rgba(108,99,255,.18), transparent 60%),
            radial-gradient(700px 500px at 90% 10%, rgba(139,92,246,.12), transparent 55%),
            #0c0e16;
    }
    #MainMenu{visibility:hidden;}footer{visibility:hidden;}
    .auth-card{background:#13152a;border:1px solid #1e2133;border-radius:18px;padding:32px 36px 8px;margin-bottom:8px;box-shadow:0 30px 60px -30px rgba(0,0,0,.6);}
    .auth-title{font-family:'Syne',sans-serif;font-size:26px;font-weight:800;color:#e2e0f0;margin-bottom:8px;letter-spacing:-.02em;}
    .auth-copy{font-size:13px;color:#8885a0;line-height:1.7;margin-bottom:18px;}
    .auth-note{font-size:11px;color:#6b6888;margin-top:-8px;margin-bottom:14px;}
    .stButton>button{background:linear-gradient(135deg,#6c63ff,#8b5cf6);color:white;border:none;border-radius:10px;padding:14px 18px;font-size:14px;width:100%;}
    .stButton>button:hover{opacity:.92;}
    .stTabs [data-baseweb="tab-list"]{background:#13152a;border-radius:12px;padding:5px;border:1px solid #1e2133;gap:3px;}
    .stTabs [data-baseweb="tab"]{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.06em;border-radius:8px;padding:8px 16px;color:#6b6888;}
    .stTabs [aria-selected="true"]{background:linear-gradient(135deg,#6c63ff,#8b5cf6)!important;color:white!important;}
    .stTextInput>div>div>input{background:#13152a!important;border:1px solid #1e2133!important;border-radius:8px!important;color:#e2e0f0!important;}
    .stTextInput label{color:#8885a0!important;font-size:12px!important;}
    .stRadio label{color:#c4c2d4!important;}
    .google-btn{display:flex;align-items:center;justify-content:center;background:#13152a;border:1px solid #2a2d45;border-radius:10px;padding:13px 18px;color:#e2e0f0!important;font-size:14px;font-weight:500;text-decoration:none!important;transition:all .2s;}
    .google-btn:hover{border-color:#6c63ff;background:#181b33;}
    </style>
    """, unsafe_allow_html=True)


def show_login_page() -> bool:
    if get_current_user():
        return True

    ensure_indexes()
    init_auth()
    _render_page_header()

    cfg = _google_config()
    if cfg is not None:
        _handle_google_callback(cfg)
        if get_current_user():
            return True

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            "<div class='auth-card'>"
            "<div class='auth-title'>ChurnGuard Pro</div>"
            "<div class='auth-copy'>Sign in to access your churn predictions and history.</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("auth_error"):
            st.error(st.session_state.auth_error)
            st.session_state.auth_error = None

        tabs = st.tabs(["Email & Password", "Continue with Google"])
        with tabs[0]:
            mode = st.radio(
                "Mode",
                ["Sign in", "Create account"],
                horizontal=True,
                label_visibility="collapsed",
                key="pw_mode_radio",
            )
            if mode == "Sign in":
                _render_login_form()
            else:
                _render_signup_form()
        with tabs[1]:
            _render_google_tab()

        st.markdown(
            "<div class='auth-note'>"
            "One account per email — the same email always maps to a single account, "
            "whether you sign in with a password or with Google.</div>",
            unsafe_allow_html=True,
        )

    return False


def require_login():
    init_auth()
    if not show_login_page():
        st.stop()
    return get_current_user()
