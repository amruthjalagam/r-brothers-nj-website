# site.json Schema v2

## _factory (factory control — NEW in v2)

| Key | Type | Values | Description |
|-----|------|--------|-------------|
| schema_version | string | "2" | Schema version; build script asserts this |
| archetype | string | "service" \| "artist" \| "medical" \| "ecommerce" | Drives module activation matrix |
| industry | string | e.g. "landscaping", "detailing", "music" | Human label for template selection scoring |
| template_variant | string | "service-a" \| "service-b" \| "service-c" \| "artist-a" \| "artist-b" | Must match a dir under website-template/variants/ |
| firecrawl_source | string | URL or "" | If non-empty, firecrawl_extract.sh writes brand.json from this URL |
| pages | array[string] | page slugs | Pages to assemble; each must have a corresponding .html source |
| modules.odoo_lead_form | bool | true/false | Injects partials/odoo-lead-form.html at <!-- MODULE:odoo-lead-form --> |
| modules.odoo_calendar | bool | true/false | Injects partials/odoo-calendar.html |
| modules.odoo_invoice | bool | true/false | Injects partials/odoo-invoice.html |
| modules.odoo_reviews | bool | true/false | Injects partials/odoo-reviews.html |
| modules.social_feed | bool | true/false | Injects partials/social-feed.html |
| modules.patient_intake | bool | true/false | Injects partials/patient-intake.html (medical archetype only) |
| animations.scroll_timeline | bool | true/false | Adds scroll-animations.css + scroll-timeline.js to every page head |
| animations.video_scrub | bool | true/false | Adds video-scrub.js; requires animations.video_src |
| animations.video_src | string | relative path or "" | Path to the Nanobanana transition video relative to site root |
| animations.reduced_motion_fallback | bool | true/false | Adds @media (prefers-reduced-motion) block; always true in production |
| brand.accent_color | string | hex | CSS var --color-accent override |
| brand.accent_hover | string | hex | CSS var --color-accent-hover override |
| brand.gold_color | string | hex | CSS var --color-gold override |
| brand.gold_hover | string | hex | CSS var --color-gold-hover override |
| brand.font_headline | string | font name | Google Fonts family name for --font-headline |
| brand.font_body | string | font name | Google Fonts family name for --font-body |
| brand.google_fonts_url | string | URL | Full ?family= Google Fonts URL |
| seo.base_url | string | https://... | Used in sitemap.xml and canonical tags |
| seo.site_name | string | text | Used in <title> suffix and OG tags |
| seo.og_image | string | path | Relative path to OG share image |
| lead_form.archetype_fields | string | "service" \| "medical" \| "artist" | Controls which lead form field set is rendered |
| lead_form.services | array[string] | service names | Populates <select> options in the lead form |
| deploy.cloudflare_project | string | CF project name | Used by deploy step |
| deploy.github_repo | string | owner/repo | Used by deploy step |
| deploy.custom_domain | string | domain or "" | Used by deploy step |

## Content keys (unchanged from v1)
brand, homepage, about, services, contact, gallery, faq — exact same structure as v1.
See content/site.json for a complete filled example (Green Haven Landscaping).

## Notes
- All boolean flags default to false. Explicitly set true only for modules the client needs.
- firecrawl_source: leave empty if client has no existing web presence or if assets are collected manually.
- template_variant must match exactly one directory under website-template/variants/. If no variants directory exists yet, value must be "base".
- lead_form.services list drives the <select> in the lead form partial — no hardcoding in HTML.
