option casemap:none
EXTERN RenderStream:PROC
.code
PUBLIC BatchAdapter
BatchAdapter PROC FRAME
 sub rsp,28h
 .allocstack 28h
 .endprolog
 lea rcx,[rsp+50h]
 mov rdx,r14
 call RenderStream
 mov rdi,r15
 mov rsi,r15
 add rsp,28h
 ret
BatchAdapter ENDP
PUBLIC Allocate
Allocate PROC
 db 048h,08bh,015h,0,0,0,0
 db 0e9h,0,0,0,0
Allocate ENDP
PUBLIC Release
Release PROC
 db 0e9h,0,0,0,0
Release ENDP
PUBLIC Clear
Clear PROC
 db 0e9h,0,0,0,0
Clear ENDP
PUBLIC Sort
Sort PROC
 db 0e9h,0,0,0,0
Sort ENDP
END
