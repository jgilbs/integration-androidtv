#!/usr/bin/env bash
# Build aarch64 distribution binary for the Android TV integration.
# Requires Docker Desktop (Windows/Mac) or Docker on Linux.
set -e

PYTHON_VER="3.11.13-0.5.0"
DOCKER_IMAGE="docker.io/unfoldedcircle/r2-pyinstaller:${PYTHON_VER}"
VERSION="$(grep '"version"' driver.json | head -1 | sed 's/.*: *"\(.*\)".*/\1/')"
ARTIFACT_NAME="uc-intg-androidtv-v${VERSION}-aarch64"

echo "==> Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Start Docker Desktop and try again."
    exit 1
fi

echo "==> Setting up QEMU for aarch64 emulation..."
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

echo "==> Building with PyInstaller (aarch64)..."
docker run --rm --name builder \
    --platform=linux/arm64/v8 \
    -v "$(pwd)":/workspace \
    "$DOCKER_IMAGE" \
    bash -c \
    "cd /workspace && \
      python -m pip install -r requirements.txt && \
      pyinstaller --clean --onedir --name intg-androidtv src/driver.py"

echo "==> Packaging artifacts..."
rm -rf artifacts
mkdir -p artifacts

echo "${VERSION}" > artifacts/version.txt
mv dist/intg-androidtv artifacts/
mv artifacts/intg-androidtv artifacts/bin
mv artifacts/bin/intg-androidtv artifacts/bin/driver
cp driver.json artifacts/
cp -r config artifacts/
cp LICENSE artifacts/

echo "==> Creating archive: ${ARTIFACT_NAME}.tar.gz"
tar czvf "${ARTIFACT_NAME}.tar.gz" -C artifacts .

echo ""
echo "Done: ${ARTIFACT_NAME}.tar.gz ($(du -sh "${ARTIFACT_NAME}.tar.gz" | cut -f1))"
echo "Upload via: Remote web configurator > Integrations > Install custom integration"
