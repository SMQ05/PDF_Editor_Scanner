# GitHub Actions Build Setup

This project uses GitHub Actions to automatically build Android APKs in a Linux environment, since Buildozer requires Linux to run.

## How It Works

The workflow (`.github/workflows/android-build.yml`) automatically builds the APK when you:
- Push to `main` or `develop` branches
- Create a pull request
- Manually trigger from GitHub Actions tab

## First-Time Setup

1. **Push your code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: PDF Scanner with PDF Viewer"
   git remote add origin https://github.com/YOUR_USERNAME/pdf-scanner-app.git
   git push -u origin main
   ```

2. **Enable GitHub Actions:**
   - Go to your repository on GitHub
   - Click "Actions" tab
   - GitHub Actions will automatically detect the workflow

3. **Trigger the build:**
   - The build will start automatically on push
   - Or go to Actions → "Android Build" → "Run workflow"

## Downloading the APK

After the build completes (~20-30 minutes for first build, ~5-10 minutes for subsequent builds):

1. Go to **Actions** tab
2. Click on the completed workflow run
3. Scroll to **Artifacts** section
4. Download `pdf-scanner-debug-apk.zip`
5. Extract and install the APK on your device

## Build Cache

The workflow caches `.buildozer` directories to speed up subsequent builds:
- First build: ~25-30 minutes
- Cached builds: ~5-10 minutes

## Creating Releases

Tag your commits to create automatic releases:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

The APK will be attached to the GitHub release automatically.

## Troubleshooting

### Build fails with "No space left on device"
- GitHub Actions runners have limited disk space
- Clear cache: Settings → Actions → Caches → Delete old caches

### Build fails with dependency errors
- Check buildozer.spec requirements match dependencies
- Verify all Java files compile correctly

### APK not found in artifacts
- Check build logs for errors
- Ensure `buildozer android debug` completed successfully

## Local Development

For local testing (requires Linux/WSL2/macOS):

```bash
buildozer android debug
```

For Windows users, use the GitHub Actions workflow for builds.
