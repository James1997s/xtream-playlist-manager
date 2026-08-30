#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
OUT="$ROOT/packages"
STAGE="$ROOT/.stage"
rm -rf "$OUT" "$STAGE"
mkdir -p "$OUT" "$STAGE/DEBIAN" "$STAGE/var/jb/Library/MobileSubstrate/DynamicLibraries" "$STAGE/var/jb/usr/share/xtplaylistcompanion"

clang -target arm64-apple-ios15.0 -fPIC -c "$ROOT/XTPlaylistCompanion/XTPlaylistCompanionBootstrap.c" -o "$ROOT/.XTPlaylistCompanion.o"
ld.lld -flavor darwin -dylib -arch arm64 -platform_version ios 15.0 15.8 -undefined dynamic_lookup -o "$ROOT/.XTPlaylistCompanion.dylib" "$ROOT/.XTPlaylistCompanion.o"
cp "$ROOT/.XTPlaylistCompanion.dylib" "$STAGE/var/jb/Library/MobileSubstrate/DynamicLibraries/XTPlaylistCompanion.dylib"
cp "$ROOT/layout/Library/MobileSubstrate/DynamicLibraries/XTPlaylistCompanion.plist" "$STAGE/var/jb/Library/MobileSubstrate/DynamicLibraries/XTPlaylistCompanion.plist"
cp "$ROOT/../companion-app/XtreamPlaylistManagerApp.swift" "$STAGE/var/jb/usr/share/xtplaylistcompanion/"
cp "$ROOT/README.md" "$STAGE/var/jb/usr/share/xtplaylistcompanion/"
cat > "$STAGE/DEBIAN/control" <<'EOF'
Package: com.james.xtplaylistcompanion
Name: XTPlaylist Companion Tweak
Version: 0.1.0-1
Architecture: iphoneos-arm64
Description: Rootless SpringBoard companion hook for XTPlaylist Companion
 A rootless iOS 15 tweak and companion source package for updating authorized Xtream playlist details on GitHub.
Maintainer: James1997s
Section: Tweaks
Priority: optional
Depends: firmware (>= 15.0)
EOF
cat > "$STAGE/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
command -v sbreload >/dev/null 2>&1 && sbreload || true
exit 0
EOF
chmod 0755 "$STAGE/DEBIAN/postinst"
dpkg-deb --root-owner-group --build "$STAGE" "$OUT/com.james.xtplaylistcompanion_0.1.0-1_iphoneos-arm64.deb"
rm -f "$ROOT/.XTPlaylistCompanion.o" "$ROOT/.XTPlaylistCompanion.dylib"
rm -rf "$STAGE"
printf '%s\n' "$OUT/com.james.xtplaylistcompanion_0.1.0-1_iphoneos-arm64.deb"
