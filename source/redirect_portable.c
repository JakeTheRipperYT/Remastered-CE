typedef unsigned long DWORD;
typedef void* HANDLE;
typedef unsigned short WCHAR;
extern const unsigned char __ImageBase;
typedef HANDLE (__stdcall *OPEN_FN)(const WCHAR*,DWORD,DWORD,void*,DWORD,DWORD,HANDLE);
static unsigned int fold(unsigned int c){if(c>='A' && c<='Z')c+=32;if(c=='/')c='\\';return c;}
static int same(const WCHAR* a,const WCHAR* b){while(*a && *b){if(fold(*a++)!=fold(*b++))return 0;}return *a==*b;}
__declspec(noinline) const WCHAR* redirect(const WCHAR* name){
 if(!name)return name;
 const WCHAR* n=name;unsigned int len=0;while(n[len])++len;
 if(len>=2 && n[0]=='.' && (n[1]=='\\'||n[1]=='/')){n+=2;len-=2;}
 if(len>=4 && n[0]=='\\' && n[1]=='\\' && n[2]=='?' && n[3]=='\\'){n+=4;len-=4;}
 #define ROUTE(file) {const WCHAR* tail=(const WCHAR*)L"\\data\\" file;const WCHAR* already=(const WCHAR*)L"\\RemasteredCE\\data\\" file;unsigned int t=0,r=0;while(tail[t])++t;while(already[r])++r;if(same(n,(const WCHAR*)L"data\\" file)||same(n,(const WCHAR*)file)||(len>=t && same(n+len-t,tail) && !(len>=r && same(n+len-r,already))))return (const WCHAR*)L"RemasteredCE\\data\\" file;}
 ROUTE(L"data.pack") ROUTE(L"shaders.pack") ROUTE(L"bp_orig.pack") ROUTE(L"web_content.pack") ROUTE(L"local_global.pack") ROUTE(L"models.pack") ROUTE(L"audio.pack")
 return name;
}
__declspec(dllexport) HANDLE __stdcall remastered_open(const WCHAR* name,DWORD access,DWORD share,void* security,DWORD disposition,DWORD flags,HANDLE template_file){
 OPEN_FN original=*(OPEN_FN*)((&__ImageBase)+0x215a530);
 if(disposition==3 && !(access&0x40000000))name=redirect(name);
 return original(name,access,share,security,disposition,flags,template_file);
}
