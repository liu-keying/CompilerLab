.class public LHelloWorld;

.super Ljava/lang/Object;

.method public static main([Ljava/lang/String;)V
    .registers 2

    add-int v1,v2,v3
    sub-int/2addr v5,v6
    return-void
    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;
    const-string	v1, "Hello World!"
    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
    return-void
.end method