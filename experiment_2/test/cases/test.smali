.class public Lcom/alipay/helloworld/MainActivity;
.super Landroid/app/Activity;
.source "MainActivity.java"


# direct methods
.method public constructor <init>()V
    .locals 0

    .prologue
    .line 7
    invoke-direct {p0}, Landroid/app/Activity;-><init>()V

    return-void
.end method


# virtual methods
.method protected onCreate(Landroid/os/Bundle;)V
    .locals 3
    .parameter "savedInstanceState"

    .prologue
    .line 11
    invoke-super {p0, p1}, Landroid/app/Activity;->onCreate(Landroid/os/Bundle;)V

    .line 12
    const/high16 v2, 0x7f03

    invoke-virtual {p0, v2}, Lcom/alipay/helloworld/MainActivity;->setContentView(I)V

    const-string v1, "92a8"

    :try_start
    invoke-static {v1}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I
    move-result v1
    :try_end
    .catch Ljava/lang/Exception;{:try_start .. :try_end}  :handler_1
    :goto_0
    return-void

    :handler_1
    move-exception v0
    invoke-virtual {v0}, Ljava/lang/Exception;->toString()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {p0, v0}, Lcom/alipay/helloworld/MainActivity;->showToastMessage(Ljava/lang/String;)V
    goto :goto_0
.end method


.method public showToastMessage(Ljava/lang/String;)V
    .locals 1
    const/4 v0, 0x01
    invoke-static {p0, p1, v0}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;
    move-result-object v0
    invoke-virtual {v0}, Landroid/widget/Toast;->show()V
    return-void
.end method

.method public static main([Ljava/lang/String;)V
    
    fill-array-data v0, :ArrayData

    :ArrayData
    .array-data 4
        0x0
        0x1
        0x2
        0x3
        0x4
    .end array-data

    .local v0, "engine":Lorg/jf/Penroser/PenroserLiveWallpaper$PenroserGLEngine;
    .local p0, "this":Lblah;
    .local v1, "future":Lcom/android/volley/toolbox/RequestFuture;, "Lcom/android/volley/toolbox/RequestFuture<Ljava/lang/Void;>;"

    :switch
    packed-switch v0, :PackedSwitch

    :PackedSwitch
    .packed-switch 10
        :Label10
        :Label11
        :Label12
        :Label13
    .end packed-switch

    :pswitch_data_c
    .packed-switch 0x0
        :pswitch_6 #case 0
        :pswitch_9 #case 1
    .end packed-switch

    packed-switch p1, :pswitch_data_c
    .end local v0
    

    sparse-switch v0, :SparseSwitch
    .end local p0
    .end local v1
    :SparseSwitch
    .sparse-switch
        10 -> :Label10
        13 -> :Label13
        15 -> :Label12
        20 -> :Label11
        99 -> :Label13
    .end sparse-switch

    :Label10
    if-nez p1, :Label13
    :Label11
    :Label12
    :Label13
.end method