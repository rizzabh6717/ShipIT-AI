# ShipIT AI Connect

Build a complete multi-page React + Tailwind CSS web app called ShipIT AI — a dark-themed AI logistics startup website. Use React Router for navigation, Framer Motion for animations, and Lucide React for icons. Use Space Grotesk (headings) and Inter (body) from Google Fonts.

DESIGN SYSTEM

Dark color palette:

Background: #080808

Surface: #101010

Surface-2: #161616

Elevated: #1C1C1C

Border: #292929

Text primary: #F5F5F5

Text secondary: #A1A1A1

Text muted: #6B6B6B

Accent (cyan-green): #00D4AA

Accent-blue (AI): #4C9EFF

Warning/amber: #FBBF24

Layout:

Centered container: max-w-[1280px] with px-6 sm:px-8 lg:px-12

8px spacing system throughout

Section vertical padding: 96px top/bottom

Shared UI components:

.btn-primary: bg #00D4AA, text #080808, uppercase, 8px radius, hover scales

.btn-secondary: bg #1C1C1C, text #F5F5F5, border #292929

glass card: bg #1C1C1C, border #292929, rounded-2xl

eyebrow label: 11px, uppercase, tracking-widest, color #6B6B6B

Aurora ambient background: fixed radial gradients of blue+cyan, z-index 0

NAVBAR (fixed, 64px tall)

Three-column grid layout: grid-cols-[auto_1fr_auto]

Left: Logo — teal square icon with a Truck icon inside, text "ShipIT AI" where "AI" is #00D4AA

Center: Nav links centered — AI Matching, How It Works, Route Marketplace, Sustainability. Active link has teal underline.

Right: Login (ghost) + Get Started (primary button) when logged out. When logged in: user avatar initial + name + email + Sign out button.

Mobile: hamburger menu with slide-down drawer containing all links + auth buttons.

PAGE 1 — LANDING PAGE (/)

Hero Section — 2-column grid lg:grid-cols-[1fr_440px], items aligned to top:

LEFT COLUMN:

Eyebrow: "Semantic route matching · pgvector · explainable AI"

H1 (huge, bold): "YOUR PACKAGE." then next line in #00D4AA: "ALREADY HAS A ROUTE."

Subtext: "ShipIT AI uses semantic route matching and explainable AI to connect your parcel with drivers already travelling your way."

Two CTA buttons side by side: Send a Parcel (primary, Sparkles icon) + Become a Driver (secondary, Truck icon)

Small trust text below: "Trusted by 2,400+ senders across Delhi-NCR · No dedicated trip, no wasted fuel"

RIGHT COLUMN:

Animated map card (h-[300px] sm:h-[360px] lg:h-[400px]), dark background with subtle grid texture

SVG inside showing: animated curved route from Delhi (bottom-left, teal dot) to Noida (top-right, white dot), passing through Rohini (amber parcel marker) and Rahul Van (blue driver dot). Moving truck glyphs along the route.

Overlaid glass pills: top-left = "LIVE" pulsing green dot + "AI Match 94% confidence" card; top-right = "Delhi → Noida · 25 km"; bottom-left = "Estimated delivery: Today, 6:30 PM"

Stats Bar (below hero): 4-cell grid, separated by #292929 borders: 94% AI Match | 86% Route Overlap | 1.3 km Detour | 2h 10m ETA. Values animate up with CountUp on scroll-in.

How ShipIT AI Works Section:

Section heading centered: "Intelligent matching for every shipment."

3 equal-height cards (min-h-[220px], flex flex-col), md:grid-cols-3:

POST — PackageCheck icon, description about posting parcel, "Explore →" link to /create-parcel

AI MATCH — Sparkles icon, description about semantic embeddings, link to /ai-matching

DELIVER — Truck icon, description about real-time tracking, link to /tracking

Cards have glass background, hover lifts with shadow

CTA Banner (bottom):

Full-width dark card bg-[#101010] rounded-3xl, py-20, px-16

H2: "Ready to see your route fill up?"

Subtext + two buttons: "I want to send →" (primary) + "I want to deliver →" (secondary)

PAGE 2 — HOW IT WORKS (/how-it-works)

3 alternating two-column rows, each row is a dark card bg-[#101010] border border-[#292929] rounded-3xl p-8:

Odd rows: text left, map right. Even rows: map left, text right (direction:rtl trick).

Each row has:

Step icon in teal square + step title (POST / AI MATCH / DELIVER) bold and large

Description paragraph in #6B6B6B

Secondary CTA button

Right side: RouteMap component showing an SVG route visualization (h-64)

The route maps show progressively more stops:

POST: Delhi → Noida

AI MATCH: Delhi → Rahul Van → Noida

DELIVER: Delhi → Pickup Rohini → Noida

PAGE 3 — AI MATCHING SHOWCASE (/ai-matching)

Two-column layout lg:grid-cols-2 with top-aligned items:

Left — AI Analysis Panel (glass card, rounded-3xl, p-8):

Header: Sparkles icon + "AI MATCH ANALYSIS" eyebrow

Big stat: ShieldCheck icon + "94%" in huge bold + "Best Driver Match" label

Progress bar: "Route overlap 86%" — animated fill on scroll

2-column mini grid: "Pickup detour: 1.3 km" | "ETA: 2h 10m"

4 reason pills (each row: icon + text):

MapPin: "Route already passes your pickup point"

Truck: "Vehicle capacity sufficient"

Star: "Driver reliability 4.9/5"

Zap: "Delivery deadline achievable"

Right — Route Visualization:

SVG route map h-[440px] showing Delhi → Rohini → Rahul Van → Noida

Caption below: "Semantic route embedding · overlap, detour, capacity & reliability scored per driver"

PAGE 4 — ROUTE MARKETPLACE (/marketplace)

Two-column layout lg:grid-cols-[0.9fr_1.1fr]:

Left — Route List (scrollable): 4 route cards, each selectable. Selected card has blue glow border. Each card shows:

Route name: Delhi → Noida (MapPin icon + ArrowRight)

Meta row: drivers count (Truck icon) | time (Clock) | distance (MapPin) | CO₂ kg (Leaf)

Price ₹120 top-right

AI match progress bar: AI match 94% in blue

Routes: Delhi→Noida (94% match), Noida→Gurgaon (81%), Delhi→Ghaziabad (78%), Gurgaon→Delhi (88%)

Right — Interactive Map (sticky):

SVG route map showing all 4 routes. Selected route is highlighted blue, others are faint white.

Below map: summary panel with selected route details (from→to, price, delivery time, distance, CO₂ saved)

PAGE 5 — SUSTAINABILITY (/sustainability)

Headline: "YOUR DELIVERY DIDN'T NEED ANOTHER TRIP." in huge bold

Comparison Grid lg:grid-cols-2:

LEFT card (glass): "Traditional delivery" — 18.6 km, "a dedicated trip just for you", route map showing straight horizontal line (faint/inactive)

RIGHT card (glass with teal border): "ShipIT AI" with Leaf icon — 4.2 km in #00D4AA, route map showing efficient shared route

Savings Grid sm:grid-cols-2:

"Km avoided: 14.4 km" (white)

"CO₂ saved: 2.8 kg" (teal)

Footer caption: "Every journey can carry something."

PAGE 6 — AUTH PAGE (/auth)

Split or centered card design. Two tabs: Login and Register.

Role selector on register: Sender or Driver (toggle pills)

Fields: Name (register only), Email, Password

Primary button: "Sign In" / "Create Account"

Dark glassmorphism card on #080808 background with aurora

Toast notifications for success/error (react-hot-toast)

AUTHENTICATED PAGES (require login)

Sender Dashboard (/sender):

Welcome header with user name

Stats row: Active Parcels, Matched, Delivered, CO₂ Saved

List of shipments — each card shows parcel ID, route, status badge (Matched/Pending/Delivered), AI match %, action buttons

Driver Dashboard (/driver):

Available route toggle (online/offline status pill)

Stats: Trips completed, Packages delivered, Rating, Earnings

List of available parcel matches — each showing parcel details, distance, payment, Accept button

Create Parcel (/create-parcel):

Multi-step or single form:

Origin city, Destination city

Package weight (kg), dimensions

Description

Delivery deadline (date picker)

Submit → calls backend POST /api/shipments

On success: show AI match results or redirect to dashboard

ANIMATIONS

Page entrance: opacity: 0, y: 16 → opacity: 1, y: 0 with staggered delays using Framer Motion

Cards: hover lifts translateY(-2px) with shadow

Map route: SVG stroke-dasharray/dashoffset draw-on animation (2.4s cubic-bezier)

Moving trucks: SVG animateMotion along route paths, repeating indefinitely

Stats: CountUp animation from 0 to final value on scroll-in (use IntersectionObserver or whileInView)

Progress bars: width animates from 0% to target on scroll-in

BACKEND API CALLS

All API requests go to http://localhost:5000/api (configurable via .env VITE_API_URL).

Endpoints used:

POST /api/auth/register — { name, email, password, role }

POST /api/auth/login — { email, password }

GET /api/shipments — list sender's shipments (auth header)

POST /api/shipments — create parcel

GET /api/drivers/matches/:shipmentId — get AI-matched drivers

GET /api/tracking/:trackingId — get tracking status

Store JWT in localStorage. Add Authorization: Bearer <token> header to all authenticated requests. Use React Context for auth state (user, login, logout, loading).

ROUTING

/ → Landing Page (redirect to /sender or /driver if logged in)

/auth → Auth Page

/how-it-works → How It Works

/marketplace → Route Marketplace

/ai-matching → AI Matching Showcase

/sustainability → Sustainability

/sender → Sender Dashboard (protected, sender only)

/driver → Driver Dashboard (protected, driver only)

/create-parcel → Create Parcel form (protected, sender only)

/tracking → Tracking Page

Protected routes redirect to /auth if not logged in. Wrong-role routes redirect to correct dashboard.

EXTRA DETAILS

All public sub-pages have pt-16 top padding to clear the fixed 64px navbar

The aurora background is a fixed position: fixed radial gradient overlay (pointer-events: none, z-index: 0) — blue top-left, teal top-right, subtle

Scrollbar styled: 8px wide, thumb #292929

Font smoothing: -webkit-font-smoothing: antialiased

All text inputs and selects have dark styling: bg #101010, border #292929, focus border #4C9EFF with blue glow ring

Mobile-first responsive: single column on mobile, 2-3 columns on desktop

No placeholder images — all visuals are SVG-based route maps and icon-driven UI

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
