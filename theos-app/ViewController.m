#import "ViewController.h"
#import <Security/Security.h>

static NSString * const kPlaylistURL = @"https://raw.githubusercontent.com/James1997s/xtream-playlist-manager/main/playlist.m3u";

@interface ViewController ()
@property(nonatomic,strong) UITextField *serverField;
@property(nonatomic,strong) UITextField *userField;
@property(nonatomic,strong) UITextField *passwordField;
@property(nonatomic,strong) UITextView *outputView;
@end

@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = @"XDREAM";
    self.view.backgroundColor = UIColor.systemBackgroundColor;
    self.serverField = [self field:@"Server URL" secure:NO];
    self.userField = [self field:@"Username" secure:NO];
    self.passwordField = [self field:@"Password" secure:YES];
    self.outputView = [[UITextView alloc] init];
    self.outputView.editable = NO;
    self.outputView.font = [UIFont monospacedSystemFontOfSize:12 weight:UIFontWeightRegular];
    self.outputView.layer.borderColor = UIColor.systemGray4Color.CGColor;
    self.outputView.layer.borderWidth = 1;
    self.outputView.layer.cornerRadius = 8;
    UIButton *test = [self button:@"Save and test connection" action:@selector(testConnection)];
    UIButton *preview = [self button:@"Generate M3U preview" action:@selector(generatePreview)];
    UIButton *copy = [self button:@"Copy public playlist URL" action:@selector(copyURL)];
    UIStackView *stack = [[UIStackView alloc] initWithArrangedSubviews:@[self.serverField,self.userField,self.passwordField,test,preview,copy,self.outputView]];
    stack.axis = UILayoutConstraintAxisVertical;
    stack.spacing = 12;
    stack.translatesAutoresizingMaskIntoConstraints = NO;
    [self.view addSubview:stack];
    [NSLayoutConstraint activateConstraints:@[
        [stack.leadingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.leadingAnchor constant:16],
        [stack.trailingAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.trailingAnchor constant:-16],
        [stack.topAnchor constraintEqualToAnchor:self.view.safeAreaLayoutGuide.topAnchor constant:16],
        [self.outputView.heightAnchor constraintGreaterThanOrEqualToConstant:220]
    ]];
    self.serverField.text = [[NSUserDefaults standardUserDefaults] stringForKey:@"server"];
    self.userField.text = [[NSUserDefaults standardUserDefaults] stringForKey:@"user"];
    self.passwordField.text = [self keychainValue:@"password"];
}

- (UITextField *)field:(NSString *)placeholder secure:(BOOL)secure {
    UITextField *f = [[UITextField alloc] init];
    f.placeholder = placeholder; f.borderStyle = UITextBorderStyleRoundedRect; f.secureTextEntry = secure;
    f.autocapitalizationType = UITextAutocapitalizationTypeNone; f.autocorrectionType = UITextAutocorrectionTypeNo;
    return f;
}
- (UIButton *)button:(NSString *)title action:(SEL)action {
    UIButton *b = [UIButton buttonWithType:UIButtonTypeSystem];
    [b setTitle:title forState:UIControlStateNormal]; b.titleLabel.font = [UIFont boldSystemFontOfSize:16];
    [b addTarget:self action:action forControlEvents:UIControlEventTouchUpInside]; return b;
}
- (NSURL *)serverURL {
    NSString *s = [self.serverField.text stringByTrimmingCharactersInSet:NSCharacterSet.whitespaceAndNewlineCharacterSet];
    if (![s hasPrefix:@"http://"] && ![s hasPrefix:@"https://"]) s = [@"http://" stringByAppendingString:s];
    while ([s hasSuffix:@"/"]) s = [s substringToIndex:s.length-1];
    return [NSURL URLWithString:s];
}
- (NSURL *)apiURLWithAction:(NSString *)action {
    NSURL *base = [self.serverURL URLByAppendingPathComponent:@"player_api.php"];
    NSURLComponents *c = [NSURLComponents componentsWithURL:base resolvingAgainstBaseURL:NO];
    c.queryItems = @[[NSURLQueryItem queryItemWithName:@"username" value:self.userField.text ?: @""], [NSURLQueryItem queryItemWithName:@"password" value:self.passwordField.text ?: @""], [NSURLQueryItem queryItemWithName:@"action" value:action]];
    return c.URL;
}
- (void)saveDetails {
    NSUserDefaults *d = NSUserDefaults.standardUserDefaults;
    [d setObject:self.serverField.text ?: @"" forKey:@"server"]; [d setObject:self.userField.text ?: @"" forKey:@"user"]; [d synchronize];
    [self setKeychain:self.passwordField.text ?: @"" key:@"password"];
}
- (void)testConnection { [self saveDetails]; [self requestAction:nil completion:^(id obj, NSError *e) { self.outputView.text = e ? [NSString stringWithFormat:@"Connection failed: %@",e.localizedDescription] : @"Saved securely. Xtream API responded successfully."; }]; }
- (void)generatePreview { [self saveDetails]; [self requestAction:@"get_live_streams" completion:^(NSArray *items, NSError *e) {
    if (e) { self.outputView.text = e.localizedDescription; return; }
    NSMutableString *m = [NSMutableString stringWithString:@"#EXTM3U\n"];
    for (NSDictionary *item in [items subarrayWithRange:NSMakeRange(0, MIN(20, items.count))]) {
        NSString *name = item[@"name"] ?: @"Channel"; NSString *sid = [item[@"stream_id"] description];
        [m appendFormat:@"#EXTINF:-1,%@\n%@/live/%@/%@/%@.m3u8\n",name,self.serverURL.absoluteString,self.userField.text,self.passwordField.text,sid];
    }
    self.outputView.text = [NSString stringWithFormat:@"Generated preview from %lu streams.\n\n%@",(unsigned long)items.count,m];
}]; }
- (void)copyURL { [UIPasteboard generalPasteboard].string = kPlaylistURL; self.outputView.text = [NSString stringWithFormat:@"Copied:\n%@",kPlaylistURL]; }
- (void)requestAction:(NSString *)action completion:(void (^)(id,NSError *))completion {
    NSURL *u = [self apiURLWithAction:action]; if (!u) { completion(nil,[NSError errorWithDomain:@"Xtream" code:1 userInfo:@{NSLocalizedDescriptionKey:@"Invalid server URL"}]); return; }
    [[[NSURLSession sharedSession] dataTaskWithURL:u completionHandler:^(NSData *data, NSURLResponse *r, NSError *e) { dispatch_async(dispatch_get_main_queue(), ^{ if(e){completion(nil,e);return;} NSError *j=nil; id o=[NSJSONSerialization JSONObjectWithData:data options:0 error:&j]; completion(o,j); }); }] resume];
}
- (void)setKeychain:(NSString *)value key:(NSString *)key { NSData *data=[value dataUsingEncoding:NSUTF8StringEncoding]; NSDictionary *q=@{(__bridge id)kSecClass:(__bridge id)kSecClassGenericPassword,(__bridge id)kSecAttrAccount:key}; SecItemDelete((__bridge CFDictionaryRef)q); NSMutableDictionary *n=[q mutableCopy]; n[(__bridge id)kSecValueData]=data; SecItemAdd((__bridge CFDictionaryRef)n,NULL); }
- (NSString *)keychainValue:(NSString *)key { NSDictionary *q=@{(__bridge id)kSecClass:(__bridge id)kSecClassGenericPassword,(__bridge id)kSecAttrAccount:key,(__bridge id)kSecReturnData:@YES,(__bridge id)kSecMatchLimit:(__bridge id)kSecMatchLimitOne}; CFTypeRef r=NULL; if(SecItemCopyMatching((__bridge CFDictionaryRef)q,&r)==errSecSuccess){NSString *s=[[NSString alloc] initWithData:(__bridge NSData *)r encoding:NSUTF8StringEncoding]; CFRelease(r); return s;} return nil; }
@end
