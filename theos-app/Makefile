TARGET := iphone:clang:15.6:14.0
ARCHS := arm64
THEOS_PACKAGE_SCHEME := rootless

include $(THEOS)/makefiles/common.mk

APPLICATION_NAME = XtreamPlaylistManager
XtreamPlaylistManager_FILES = main.m AppDelegate.m ViewController.m
XtreamPlaylistManager_FRAMEWORKS = UIKit Foundation Security
XtreamPlaylistManager_CFLAGS = -fobjc-arc
TARGET_LD = /usr/bin/clang++
XtreamPlaylistManager_LDFLAGS = -fuse-ld=/usr/bin/ld64.lld-18 -Wl,-platform_version,ios,14.0,15.6 -Wl,-arch,arm64

include $(THEOS_MAKE_PATH)/application.mk

after-install::
	install.exec "sbreload"
