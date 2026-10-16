typedef unsigned long DWORD;
typedef int BOOL;
typedef void* HANDLE;
typedef unsigned short WORD;
typedef unsigned char BYTE;
typedef unsigned short WCHAR;
typedef struct {DWORD cb;WCHAR* reserved;WCHAR* desktop;WCHAR* title;DWORD x,y,xsize,ysize,xchars,ychars,fill,flags;WORD show,reserved2;BYTE* reservedptr;HANDLE input,output,error;} STARTUP;
typedef struct {HANDLE process,thread;DWORD pid,tid;} PROCESS;
__declspec(dllimport) DWORD __stdcall GetModuleFileNameW(HANDLE,WCHAR*,DWORD);
__declspec(dllimport) BOOL __stdcall SetEnvironmentVariableW(const WCHAR*,const WCHAR*);
__declspec(dllimport) BOOL __stdcall CreateProcessW(const WCHAR*,WCHAR*,void*,void*,BOOL,DWORD,void*,const WCHAR*,STARTUP*,PROCESS*);
__declspec(dllimport) BOOL __stdcall CloseHandle(HANDLE);
__declspec(dllimport) void __stdcall ExitProcess(DWORD);
__declspec(dllimport) int __stdcall MessageBoxW(HANDLE,const WCHAR*,const WCHAR*,unsigned int);
static WCHAR root[32768],exe[32768];
static STARTUP startup;
static PROCESS process;
void entry(void){
 DWORD n=GetModuleFileNameW(0,root,32768),i,j;
 if(!n || n>=32700)goto error;
 i=n;while(i && root[i-1]!='\\')--i;
 if(!i)goto error;
 root[i]=0;
 for(j=0;j<i;++j)exe[j]=root[j];
 {const WCHAR* name=(const WCHAR*)L"RemasteredCE\\shogun2_complete_edition.exe";j=0;do{exe[i+j]=name[j];}while(name[j++]);}
 if(!SetEnvironmentVariableW((const WCHAR*)L"SteamAppId",(const WCHAR*)L"3846830"))goto error;
 if(!SetEnvironmentVariableW((const WCHAR*)L"SteamGameId",(const WCHAR*)L"3846830"))goto error;
 startup.cb=sizeof(startup);
 if(!CreateProcessW(exe,0,0,0,0,0,0,root,&startup,&process))goto error;
 CloseHandle(process.thread);CloseHandle(process.process);ExitProcess(0);
error:
 MessageBoxW(0,(const WCHAR*)L"Unable to start Remastered CE. Keep this launcher in the CE installation folder alongside RemasteredCE_Bootstrap.exe, and make sure Steam is running.",(const WCHAR*)L"Remastered CE",0x10);ExitProcess(1);
}
