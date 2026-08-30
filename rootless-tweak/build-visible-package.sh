#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO=$(CDPATH= cd -- "$ROOT/.." && pwd)
OUT="$ROOT/packages"
STAGE="$ROOT/.visible-stage"
OLD="$REPO/jailbreak/com.james.xtream-playlist-manager_0.1.0_iphoneos-arm64.deb"
rm -rf "$STAGE"
mkdir -p "$OUT" "$STAGE"
clang -target arm64-apple-ios15.0 -fPIC -c "$ROOT/XTPlaylistCompanion/XTPlaylistCompanionBootstrap.c" -o "$ROOT/.XTPlaylistCompanion.o"
ld.lld -flavor darwin -dylib -arch arm64 -platform_version ios 15.0 15.8 -undefined dynamic_lookup -o "$ROOT/.XTPlaylistCompanion.dylib" "$ROOT/.XTPlaylistCompanion.o"
dpkg-deb -x "$OLD" "$STAGE"
cp "$REPO/theos-app/Resources/Info.plist" "$STAGE/var/jb/Applications/XtreamPlaylistManager.app/Info.plist"
mkdir -p "$STAGE/var/jb/Library/MobileSubstrate/DynamicLibraries" "$STAGE/var/jb/usr/share/xtplaylistcompanion"
cp "$ROOT/.XTPlaylistCompanion.dylib" "$STAGE/var/jb/Library/MobileSubstrate/DynamicLibraries/XTPlaylistCompanion.dylib"
cp "$ROOT/layout/Library/MobileSubstrate/DynamicLibraries/XTPlaylistCompanion.plist" "$STAGE/var/jb/Library/MobileSubstrate/DynamicLibraries/XTPlaylistCompanion.plist"
cp "$REPO/companion-app/XtreamPlaylistManagerApp.swift" "$STAGE/var/jb/usr/share/xtplaylistcompanion/"
cp "$ROOT/README.md" "$STAGE/var/jb/usr/share/xtplaylistcompanion/README.md"
mkdir -p "$STAGE/DEBIAN"
cat > "$STAGE/DEBIAN/control" <<'EOF'
Package: com.james.xtplaylistcompanion
Name: XDREAM
Version: 0.1.4
Architecture: iphoneos-arm64
Description: Unsigned rootless XDREAM Xtream companion app and SpringBoard tweak
 A rootless iOS 15 companion package with an arm64 UIKit app bundle and tweak payload.
Maintainer: James1997s
Section: Utilities
Priority: optional
Depends: firmware (>= 15.0)
EOF
cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
# Do not run uicache or respring during dpkg/Sileo installation.
# Run them manually after the transaction completes if needed.
exit 0
EOF
chmod 0755 "$STAGE/DEBIAN/postinst"
dpkg-deb --root-owner-group --build "$STAGE" "$OUT/com.james.xtplaylistcompanion_0.1.4_iphoneos-arm64.deb"
rm -rf "$STAGE" "$ROOT/.XTPlaylistCompanion.o" "$ROOT/.XTPlaylistCompanion.dylib"
printf '%s\\n' "$OUT/com.james.xtplaylistcompanion_0.1.4_iphoneos-arm64.deb"
