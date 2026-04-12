# Template Inventory

Source of truth for page counts, module state, and variant diffs across all template repos.

## Base: website-template (7 pages)

Pages: index, about, services, contact, faq, gallery, account
CSS: variables.css, reset.css, style.css, animations.css
JS: cms-loader.js, nav.js, scroll.js, odoo-lead-form.js, odoo-calendar.js, odoo-invoice.js, odoo-invoice-portal.js
Modules wired: account.html (data-module)

## Service Variant A: r-brothers-website (11 root + 12 areas + 6 services + 18 blog = 47 pages)

Root pages: index, about, services, contact, faq, gallery, pricing, reviews, testimonials, scroll-test, 404
Areas: aberdeen, east-brunswick, edison, freehold, manalapan, matawan, metuchen, north-brunswick, old-bridge, piscataway +2
Services: fencing, landscaping, lawn-care, power-washing, sod, tree-service
Blog: 18 posts (aeration guide, fence materials, commercial landscaping, etc.)
Extras vs base: pricing.html, reviews.html, testimonials.html, 404.html, areas/, services/, blog/
Scroll prototype: scroll-test.html (5 techniques — reference only, do NOT ship)
Modules wired: contact.html, index.html (odoo-lead-form)
JS extras: none (no odoo-invoice.js — simpler variant)

## Service Variant B: air-duct-website (7 root + 13 areas + 5 services + 10 blog = 35 pages)

Root pages: index, about, services, contact, faq, gallery, pricing
Areas: 13 (edison-nj, indianapolis, middlesex, monmouth, etc.)
Services: commercial, dryer-vent, mold-remediation, residential, sanitization
Blog: 10 posts
Extras vs base: pricing.html, areas/, services/, blog/
Modules wired: none (no data-module attributes)
JS: no Odoo JS files (cms-loader, nav, scroll only)

## Service Variant C: fencing-website (8 root + 26 areas + 7 services + 10 blog = 51 pages)

Root pages: index, about, services, contact, faq, gallery, pricing, testimonials
Areas: 26 (carteret, cranbury, east-brunswick, edison, freehold, etc.)
Services: aluminum-fence, chain-link, commercial-fencing, deer-fencing, gates, vinyl-fence, wood-fence
Blog: 10 posts
Extras vs base: pricing.html, testimonials.html, areas/, services/, blog/
Modules wired: none
JS: no Odoo JS files

## Artist Variant A: music-instructor-website (8 pages)

Root pages: index, about, services, contact, faq, gallery, privacy, terms
Extras vs base: privacy.html, terms.html (no portfolio.html)
Modules wired: none
JS: no Odoo JS files

## Artist Variant B: portfolio-website (5 pages)

Root pages: index, about, contact, faq, portfolio
Extras vs base: portfolio.html
Missing vs base: services.html, gallery.html, account.html
Modules wired: none
JS: no Odoo JS files

## Common Across All Variants

CSS (identical filenames): variables.css, reset.css, style.css, animations.css
JS (shared): cms-loader.js, nav.js, scroll.js
Content: site.json (CMS data — only in website-template base)

## Module Integration Gap

Only r-brothers-website and website-template have Odoo JS wired.
All other variants (air-duct, fencing, music, portfolio) have NO module integration.
Gap is integration/assembly, not component quality — JS files exist in base, need injection.
