# C4 Architecture Walkthrough — Technical Speaker Notes
## RSS Summarizer with Okta IDP Integration

---

## Slide 1: System Context Diagram (c4-system-context.drawio)

**Purpose:** Highest-level view. Shows the RSS Summarizer as a single box and everything around it — people and external systems.

**Opening:**
"Let's start at the 30,000-foot view. This diagram answers one question: who interacts with our system and what does it depend on?"

**Key talking points:**

- **Two distinct user personas** — we've separated them intentionally because they have fundamentally different access levels:
  - **News Reader (Regular User):** Authenticated through Okta with a `user` role claim. They get the dashboard — read-only. They can view summarized articles, provide feedback on articles, and search. That's the boundary of their access.
  - **Administrator (Admin Role):** Also authenticated through Okta, but with an `admin` role claim. Full access to the Admin Console — manages RSS feeds, topics, categories, scheduler configuration, and LLM settings.

- **Okta Identity Provider (purple box):** This is the new addition. Okta sits as an external system handling both AuthN and AuthZ:
  - AuthN via OIDC/OAuth 2.0 — standard authorization code flow
  - AuthZ via role claims embedded in the ID token — Okta groups map to `admin` or `user` roles
  - Both user types authenticate through Okta before they ever touch our system. The purple arrows represent auth flows.

- **Okta → System relationship (thick purple arrow):** Okta validates tokens and provides role claims back to the RSS Summarizer via OIDC/OAuth 2.0. This is the trust boundary — our system trusts Okta as the identity authority.

- **RSS News Feeds (grey):** External sources — BBC, Reuters, Bloomberg, etc. The system fetches from these. No auth change here.

- **AWS Bedrock (grey):** Claude AI for article analysis and summarization. Also unchanged — this is a backend service call, not user-facing.

**Transition:** "Now that we see who's involved, let's zoom into the AWS deployment and see how traffic actually flows."

---

## Slide 2: AWS System Context (c4-level1-context.drawio)

**Purpose:** Same C1 level but overlaid on the AWS infrastructure. Shows the network path from user → Okta → AWS → application.

**Opening:**
"Same actors, but now we're looking at the actual AWS deployment topology and how the auth flow maps to infrastructure."

**Key talking points:**

- **Auth flow (purple arrows, left side):**
  1. Regular Users and Admin Users both initiate OIDC AuthN against Okta (purple arrows going right to the Okta box)
  2. Okta authenticates the user, issues an ID token with role claims
  3. After auth, the browser redirects with the token to Route 53 (the "Redirect with ID token + roles" arrow from Okta → Route 53)
  4. From there it's standard AWS networking: Route 53 → ALB → EC2

- **Token validation (dashed purple arrow):** The system in the private subnet validates tokens back against Okta via OIDC Discovery. This is a runtime call — the Flask app fetches Okta's JWKS endpoint to verify token signatures. This is the dashed line from the system back to Okta.

- **AWS boundary (orange dashed):** Everything inside is within the AWS Cloud landing zone. The system sits in a VPC private subnet — not directly internet-accessible.

- **Network path for data:**
  - EC2 → Bedrock via IAM Role (no internet traversal, stays within AWS)
  - EC2 → Internet Gateway → RSS feeds (outbound HTTPS for fetching articles)

- **Security note:** The EC2 instance in the private subnet never receives direct internet traffic. All inbound goes through ALB with security groups. The only outbound internet path is through the IGW for RSS fetching and Okta token validation.

**Transition:** "Let's crack open the AWS boundary and look at what containers are running inside."

---

## Slide 3: Container Diagram (c4-level2-container.drawio)

**Purpose:** Zooms into the AWS deployment to show the individual containers/services and how they communicate. This is where the Okta middleware becomes visible as a distinct component.

**Opening:**
"Now we're inside the AWS boundary. This diagram shows every deployable unit and how the auth middleware fits into the request pipeline."

**Key talking points:**

- **Auth flow end-to-end:**
  1. Both user types perform OIDC login against Okta (purple arrows on the left)
  2. After auth, requests arrive with tokens via HTTPS → Route 53 → ALB (port 443, SSL termination)
  3. ALB forwards to EC2 on port 5000 (security group restricted to ALB SG only)
  4. Inside EC2, the first thing that touches the request is the **Okta OIDC Middleware**

- **Okta OIDC Middleware (purple box inside private subnet):** This is a Flask extension that:
  - Validates the bearer token on every request
  - Calls back to Okta via OIDC Discovery to verify token signatures (dashed purple arrow back to Okta)
  - Extracts role claims from the token
  - Manages the server-side session

- **Role-based routing (blue arrows from middleware):**
  - `user` role → routes to **User Dashboard** container (read-only news view, article feedback, search)
  - `admin` role → routes to **Admin Console** container (manage feeds, topics, categories, scheduler, LLM config)
  - This is the key architectural decision: the middleware acts as a gatekeeper before any business logic executes

- **Middleware → Flask Web App:** After auth, the middleware delegates to the core Flask app for business logic (services, models, data access)

- **Data tier:**
  - Flask Web App → SQLite (reads/writes on local EC2 storage)
  - Flask Web App → AWS Bedrock via HTTPS (AI analysis, authorized via IAM Role)

- **Security groups (orange annotation boxes):**
  - ALB SG: Inbound 443 from internal Fed IPs
  - EC2 SG: Inbound 5000 from ALB SG only — defense in depth

**Transition:** "Let's go one level deeper and look at the components inside the Flask application itself."

---

## Slide 4: Component Diagram (c4-level3-component.drawio)

**Purpose:** Inside the Flask Web Application container. Shows every internal component, the auth pipeline, and how role enforcement works at the code level.

**Opening:**
"We're now inside the Flask application on the EC2 instance. This is where you see exactly how the auth pipeline is wired and which components are protected by which roles."

**Key talking points:**

- **Request pipeline (left to right):**
  1. ALB → **Okta OIDC Middleware** (auth.py) — first component to handle the request
  2. Middleware → **Role Guard** (auth.py) — extracts role from Okta claims, enforces access
  3. Role Guard branches:
     - `user` or `admin` role → **Dashboard Routes** (app.py) — the `/` dashboard view, article feedback, search
     - `admin` role only → **Admin Console Routes** (app.py) — feeds, topics, categories, scheduler, LLM config management

- **Okta OIDC Middleware (purple):** Handles the OIDC callback, token validation, and session management. Communicates back to external Okta IDP for OIDC Discovery and token validation (dashed purple arrow to Okta IDP on the left).

- **Role Guard (purple):** Implements the `@require_role` decorator pattern. This is the enforcement point — if a user with `user` role tries to hit an admin route, they get a 403. The Role Guard also stores the **User Session** (purple box below it) — contains the Okta user profile and role.

- **Route separation:**
  - **Dashboard Routes** — accessible to both roles. Renders via Jinja2 templates. Read-only operations.
  - **Admin Console Routes** — admin only. This is where all the write operations live: add/delete feeds, topics, categories, trigger news refresh, configure scheduler, update LLM settings.
  - Both route groups render through the shared **Templates** component (Jinja2).

- **Service layer (right side, unchanged):**
  - Admin Console Routes → **News Processor** (orchestrates the pipeline)
  - News Processor → **RSS Fetcher** → **Content Scraper** → Internet Gateway
  - News Processor → **AI Analyzer** → AWS Bedrock

- **Data models (bottom):**
  - Feed Model, Topic Model, Article Model — all persist to SQLite
  - Admin routes interact with Feed Model directly (CRUD operations)
  - News Processor writes to Article Model after AI analysis

**Transition:** "Finally, let's look at the code-level class diagram to see the exact interfaces and data structures."

---

## Slide 5: Code Diagram (c4-level4-code.drawio)

**Purpose:** Class-level detail. Shows every class, its attributes, methods, and relationships. This is the implementation blueprint.

**Opening:**
"This is the implementation view — the class diagram. If you're a developer picking this up, this is your map. The left side is all new Okta auth code, the right side is the existing business logic."

**Key talking points:**

- **Auth classes (purple, left column) — all new:**

  - **OktaConfig** (Configuration): Holds all Okta connection parameters — domain, client ID/secret, issuer URL, redirect URI, scopes. These come from environment variables.

  - **OktaOIDCMiddleware** (Middleware): The core auth engine.
    - Takes OktaConfig and a PyJWKClient (for JWKS key fetching)
    - `login()` — redirects to Okta's authorize endpoint
    - `callback()` — handles the OIDC redirect, exchanges auth code for tokens, creates session
    - `validate_token()` — verifies JWT signature using Okta's public keys
    - `get_user_roles()` — extracts role claims from the decoded token
    - `is_authenticated()` — session check for subsequent requests

  - **RoleGuard** (Decorator): The authorization enforcement layer.
    - Defines a `Roles` enum: `ADMIN`, `USER`
    - `require_role(role)` — Python decorator that wraps route handlers. Checks the session role against the required role.
    - `require_admin()` — convenience shortcut for `require_role(ADMIN)`
    - `require_authenticated()` — just checks login, no role requirement
    - `get_current_user()` — returns the UserSession from the Flask session

  - **UserSession** (ValueObject): What gets stored in the session after auth.
    - email, name, role, okta_id, groups
    - `is_admin()` — helper method

  - **Auth Routes** (Controller): The HTTP endpoints for the auth flow itself.
    - `/login` — redirect to Okta
    - `/callback` — process OIDC response
    - `/logout` — clear session
    - `/unauthorized` — 403 page

- **Controller split (green, right side):**

  - **Dashboard Routes** — annotated `[Requires: user or admin role]`
    - `dashboard()`, `article_feedback()`, `generate_markdown()`, `generate_html()`
    - These are the only routes a regular user can access

  - **Admin Console Routes** — annotated `[Requires: admin role only]`
    - Full CRUD: `admin_feeds()`, `admin_topics()`, `admin_categories()`, `admin_llm()`, `admin_scheduler()`
    - Write operations: `add_feed()`, `add_topic()`, `add_category()`, `delete_*()`, `refresh_news()`, `clear_all_news()`, `update_llm_config()`, `update_schedule()`
    - Every one of these is wrapped with `@require_admin`

- **Relationship highlights:**
  - RoleGuard **protects** Dashboard Routes (dashed purple arrow)
  - RoleGuard **protects (admin)** Admin Console Routes (dashed purple arrow)
  - OktaOIDCMiddleware **uses** OktaConfig and **delegates** to RoleGuard
  - RoleGuard **creates** UserSession
  - OktaOIDCMiddleware **uses** the Okta OIDC SDK (PyJWKClient, jwt.decode, OAuth2Session) — external dependency

- **Existing classes (unchanged):**
  - Entity layer: Feed, Category, Topic, Article — same schema as before
  - Service layer: RSSFetcher, AIService, NewsProcessor — same business logic
  - External libs: feedparser, Boto3 BedrockClient

- **Auth flow summary (from the note box on the diagram):**
  1. User hits `/login` → redirect to Okta
  2. Okta authenticates → OIDC callback
  3. OktaOIDCMiddleware validates token
  4. RoleGuard extracts role from claims
  5. `admin` role → Admin Console routes
  6. `user` role → Dashboard routes only
  7. Unauthorized → 403 page

---

## General Presentation Tips

- **Color coding is consistent across all diagrams:**
  - Purple = Okta / auth-related (new)
  - Blue = our system / internal components
  - Orange = AWS infrastructure services
  - Grey = external systems
  - Green = controller/route classes (code level)
  - Yellow = service classes (code level)
  - Red = external libraries (code level)

- **The auth boundary is always the first thing traffic hits** after the ALB. Emphasize this — no request reaches business logic without passing through Okta validation.

- **Admin vs User is enforced at the middleware level**, not at the UI level. Even if someone crafts a direct HTTP request to an admin endpoint, the RoleGuard decorator will reject it with a 403.

- **Okta is the single source of truth for identity and roles.** The application never stores passwords or manages user accounts. Group membership in Okta determines what you can do in the app.
