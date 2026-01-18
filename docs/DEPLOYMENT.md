# IG Reports Bot - Deployment Guide

## GitHub Pages Setup

### 1. Enable GitHub Pages

1. Go to your repository on GitHub: `https://github.com/YOUR_USERNAME/ig-reports-bot`
2. Click **Settings** tab
3. Scroll down to **Pages** section (in left sidebar)
4. Under **Source**, select:
   - Branch: `main` (or `master`)
   - Folder: `/docs`
5. Click **Save**

### 2. Wait for Deployment

- GitHub will automatically build and deploy your site
- This usually takes 1-2 minutes
- Your site will be available at: `https://YOUR_USERNAME.github.io/ig-reports-bot/`

### 3. Verify Deployment

- Visit your site URL
- Check that reports are displaying correctly
- Test filtering and sorting functionality

### 4. Update Website

To update the website with new reports:

```bash
# Run the daily pipeline (scrape + filter + summarize)
python run_daily.py

# Rebuild the website
python -m web.build --days-back 30

# Commit and push
git add docs/
git commit -m "Update website with new reports"
git push origin main
```

The website will automatically update within 1-2 minutes.

## Automation

The GitHub Actions workflow will automatically rebuild the website after each daily scrape.

See `.github/workflows/daily.yml` for the automation configuration.

## Custom Domain (Optional)

To use a custom domain:

1. Add a `CNAME` file to `docs/` with your domain:
   ```
   igreports.yourdomain.com
   ```

2. Configure DNS with your domain provider:
   - Add a CNAME record pointing to `YOUR_USERNAME.github.io`

3. Enable HTTPS in GitHub Pages settings

## Troubleshooting

### Site Not Loading
- Check GitHub Pages settings
- Verify `docs/` folder exists and has `index.html`
- Check browser console for errors

### Data Not Showing
- Verify `docs/data/reports.json` exists
- Check browser network tab for failed requests
- Run `python -m web.build` to rebuild

### Updates Not Appearing
- Wait 1-2 minutes for GitHub Pages to rebuild
- Clear browser cache
- Check GitHub Actions tab for deployment status

## Local Testing

To test the website locally:

```bash
# Build the website
python -m web.build

# Serve with Python
cd docs
python -m http.server 8000

# Open in browser
open http://localhost:8000
```

## Website Features

✅ **Responsive Design** - Works on mobile, tablet, and desktop
✅ **Real-time Filtering** - Search, filter by agency, newsworthy status
✅ **Sorting** - By date or newsworthy score
✅ **Statistics** - Total reports, newsworthy count, posted count
✅ **Rich Details** - LLM reasoning, topics, dollar amounts
✅ **Direct Links** - Click through to original reports
✅ **Fast Loading** - Static JSON data, no backend needed

## Cost

**GitHub Pages is 100% free** for public repositories! 🎉
