option casemap:none
EXTERN MergeAdjacent:PROC
.code
PUBLIC BatchAdapter
BatchAdapter PROC FRAME
    sub rsp,28h
    .allocstack 28h
    .endprolog
    ; Call-site RSP +20h is the completed native concurrent_vector.
    lea rcx,[rsp+50h]
    call MergeAdjacent
    ; Replay the two instructions replaced at the call site.
    mov rdi,r15
    mov rsi,r15
    add rsp,28h
    ret
BatchAdapter ENDP
PUBLIC Append
Append PROC
    db 0e9h,0,0,0,0
Append ENDP
END
