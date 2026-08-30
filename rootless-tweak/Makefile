ARCHS := arm64
TARGET := iphone:clang:15.0:15.8
THEOS_PACKAGE_SCHEME := rootless

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = XTPlaylistCompanion
XTPlaylistCompanion_FILES = XTPlaylistCompanion/XTPlaylistCompanion.m
XTPlaylistCompanion_FRAMEWORKS = Foundation
XTPlaylistCompanion_CFLAGS = -fobjc-arc
XTPlaylistCompanion_INSTALL_TARGET_PROCESSES = SpringBoard

include $(THEOS_MAKE_PATH)/tweak.mk

after-install::
	install.exec "sbreload"
