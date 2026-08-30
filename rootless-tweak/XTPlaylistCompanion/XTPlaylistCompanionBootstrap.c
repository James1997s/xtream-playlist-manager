typedef unsigned long size_t;
extern int open(const char *, int, ...);
extern long write(int, const void *, size_t);
extern int close(int);

#define O_WRONLY 1
#define O_CREAT 64
#define O_TRUNC 512

__attribute__((constructor)) static void xtpc_loaded(void) {
    const char marker[] = "1\n";
    int fd = open("/var/mobile/Library/Preferences/com.james.xtplaylistcompanion.loaded", O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (fd >= 0) {
        (void)write(fd, marker, sizeof(marker) - 1);
        (void)close(fd);
    }
}
