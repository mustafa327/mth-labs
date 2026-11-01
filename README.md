# MTH Labs

A custom, dependency-free software and game-development portfolio for **Mustafa Thaeer**.

- Contact: **mustafathaear97@gmail.com**
- Repository: https://github.com/mustafa327/mth-labs
- Intended GitHub Pages URL: https://mustafa327.github.io/mth-labs/ (not live until Pages is enabled)

## Included

Responsive one-page portfolio, original SVG identity and illustrations, four service areas, representative project stories, an OceanBond development feature, founder profile, FAQs, email enquiry builder, privacy information, custom 404 page, accessible navigation and reduced-motion support. No libraries, npm install, paid APIs, analytics, cookies, remote fonts or server are required.

The enquiry builder **does not send email**. It creates a draft and offers an email-app link, a Gmail compose link, copy, and a plain-text download. The visitor must send the email. No banking details are published.

## Hosting: read before launch

The source can stay on GitHub regardless of the host. GitHub Pages has commercial-use restrictions: it is not intended or allowed as free hosting for running an online business, e-commerce, primarily commercial-transaction sites, or commercial SaaS. This project is an informational developer portfolio with email contact, not a storefront or SaaS; do not assume that removing checkout alone guarantees policy eligibility. Review the current terms for your intended use. For a sales-focused business website, consider Cloudflare Pages with this same GitHub repository.

Official sources (checked 1 November 2026):
- GitHub limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- GitHub publishing settings: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
- Cloudflare static HTML setup: https://developers.cloudflare.com/pages/framework-guides/deploy-anything/

### GitHub Pages: static portfolio deployment

1. Open https://github.com/mustafa327/mth-labs/settings/pages
2. Under **Build and deployment**, select **Deploy from a branch**.
3. Set branch to **main** and folder to **/(root)**, then **Save**.
4. Check the repository's **Actions** tab and the Pages settings for deployment status.
5. Once GitHub confirms deployment, open https://mustafa327.github.io/mth-labs/

`.nojekyll` disables Jekyll processing. Future commits to `main` publish through the configured branch deployment. There is no custom workflow and no secret token is needed. Repository settings must be enabled by an account with the required permissions; source files alone do not activate Pages.

### Cloudflare Pages: deploy the same repository

In Cloudflare's **Workers & Pages**, create a **Pages** project and import `mustafa327/mth-labs` from GitHub. Use production branch `main`, framework preset **None**, build command `exit 0`, and build output directory `.` (the repository root). No environment variables are required. Review the selected plan and terms before deploying.

After choosing a different public URL, update the canonical and `og:url` entries in `index.html`, and the URLs in `sitemap.xml`. On Cloudflare the 404 page links to `/` automatically. Leave optional analytics disabled to keep the privacy note accurate.

## Preview locally

From this folder:

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. It also works as a simple static folder. Clipboard buttons may be unavailable outside HTTPS or localhost; the text-selection and download fallbacks remain available. Browser or mail-client URL-length limits can affect very long email drafts; use copy/download in that case.

## Edit the content

| File | Purpose |
| --- | --- |
| `index.html` | Sections, project copy, contact fields and SEO metadata |
| `assets/site.css` | Colors, layout, responsive styles and reduced motion |
| `assets/site.js` | Mobile menu, service selection and email-draft builder |
| `assets/mark.svg` | Original vector logo / favicon |
| `brand/wordmark.svg` | Full transparent wordmark for dark backgrounds |
| `brand/wordmark-light.svg` | Full wordmark for light backgrounds |
| `privacy.html` | Actual site/contact data-handling explanation |
| `404.html` | Standalone error page |
| `sitemap.xml` | Canonical page URLs; update when moving hosts |

To change the email, replace `mustafathaear97@gmail.com` in HTML and `assets/site.js`. All asset links are relative so the site works at `/mth-labs/` or a custom domain root. Fonts use the visitor's system; no font files are bundled.

## Content and business checklist

- The site honestly presents an independent developer, not a large agency. Czechia is the base; Jordan and Iraq are remote focus markets, not claimed offices.
- No client names, logos, testimonials, private code, confidential data or invented performance metrics are included.
- Dashboard and architecture visuals are explicitly illustrative. OceanBond is explicitly in development, and its artwork is not a gameplay screenshot.
- Project descriptions summarize the developer's supplied experience. Before sharing with clients, review each claim and replace illustrations with publishable screenshots only when you have permission.
- MTH Labs is a working brand, not a claim of trademark clearance or company registration. Verify name/domain rights and applicable business-registration, legal-notice, tax and invoicing requirements before trading. The privacy page is a technical description, not a guarantee of legal compliance.
- Keep contracts, payments and banking information private. Never commit passwords, tokens or customer data.

## Ownership

Custom site source and original vector artwork prepared for Mustafa Thaeer / MTH Labs. No third-party font files or stock assets are included. No open-source license is granted by this README; choose a license intentionally before inviting reuse.
