# Xserver migration

Target: https://miraiz.sofi-school.com/
Source: commit 06f24c5de95823d012eb2551d4e0d3f877793df5
Document root: /sofi-school.com/public_html/miraiz.sofi-school.com/

Static HTML/CSS/JavaScript only; no API, database, authentication or build runtime.
Contact form opens the visitor's mail composer. It does not deliver mail on the server.
External dependency: Google Fonts. System font fallback exists.

Deploy only index.html, assets/, robots.txt, sitemap.xml and .htaccess.
Canonical, Open Graph and structured data URLs use the new HTTPS origin.
Existing parent website and mail files must not be overwritten.
Existing apex, www, wildcard, MX, SPF, DKIM and NS records must remain unchanged.

## Backup and rollback
Original website is preserved in Git at the source commit and on Vercel.
The target subdomain did not previously exist. Its new dedicated directory isolates the release.
Before replacing any future release, download/archive the target directory outside public_html.
To roll back a faulty release, restore the prior directory contents; leave parent domain and mail untouched.
During initial migration, direct visitors back to the unchanged Vercel URL if needed.
Do not delete the Vercel deployment until the new site passes HTTPS, images, mobile navigation,
FAQ, anchor links and form validation checks. Vercel is not a runtime dependency after migration.
