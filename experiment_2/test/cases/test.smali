.class public LHelloWorld;

.super Ljava/lang/Object;

.method public static main([Ljava/lang/String;)V
    .registers 2

    #add-int v1,v2,v3
    #sub-int/2addr v5,v6
    #neg-long v6,v7
    #int-to-double p8,p9
    #add-int/lit16 v0, v1, 12345
    #rsub-int v7,v100,0x123
    mul-int/lit16 v1, v2,10

    iput-boolean v0, p0, Lcom/disney/xx/XxActivity;->isRunning:Z
    sput v0, Lblah;->blah:Lblah;
    sget-object v0, Lcom/disney/xx/XxActivity;->PREFS_INSTALLATION_ID:Ljava/lang/String;
    sget-object v0, Ljava/lang/System;->o<ref>ut:Ljava/io/PrintStream;
    sget v0, Lblarg;->blort:I

    #invoke-virtual {p0, v2}, Lcom/disney/xx/XxActivity;->getPreferences(I)Landroid/content/SharedPreferences; 
    #return-void

    #const-string	v1, "Hello World!"
    #invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
.end method