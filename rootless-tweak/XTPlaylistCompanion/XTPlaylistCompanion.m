#import <Foundation/Foundation.h>

// New rootless companion tweak. It adds a lightweight URL-scheme handoff so
// supported apps or Shortcuts can open the companion editor without injecting
// credentials into third-party processes.

__attribute__((constructor)) static void XTPCLoad(void) {
    @autoreleasepool {
        NSString *directory = @"/var/mobile/Library/Preferences";
        NSString *marker = [directory stringByAppendingPathComponent:@"com.james.xtplaylistcompanion.loaded"];
        [@"1\n" writeToFile:marker atomically:YES encoding:NSUTF8StringEncoding error:nil];
    }
}
