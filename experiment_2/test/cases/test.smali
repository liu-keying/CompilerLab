.class public LHelloWorld;

.super Ljava/lang/Object;

.method public static main([Ljava/lang/String;)V
    .registers 2

    nop

    const/4 v0, 0x5 #数组长度赋值给v0寄存器
    new-array v0, v0, [I #创建指定类型[I即int数组，长度为v0即5，并将数组引用赋值于v0寄存器
    fill-array-data v0, :array_18 #用指定标记array_18处的数据填充数组
    iput-object v0, p0, Lcom/erlin/smali/SmaliParse;->intArray:[I #为数组赋值
    return-void

    const-string v1, "Hello World!"

    check-cast v1, Lcom/erlin/smali/SmaliParse$InnerClassExtends;
    instance-of v2, v0, Lcom/erlin/smali/SmaliParse$InnerClassExtends;

    const/4 v3, 0x3 #将0x3寄存给v3寄存器
    new-array v0, v3, [I #创建[I类型长度为v3寄存器数组，引用赋值给v0寄存器
    fill-array-data v0, :array_1a #用array_1a标记处数据，赋值于v0寄存器

    array-length v1, v0 #获取v0寄存器长度，赋值给v1寄存器
    new-array v2, v1, [Ljava/lang/String;

    const/4 v3, 0x0
    const-string v4, "A"
    aput-object v4, v2, v3 #v4寄存器值，赋值给v2寄存器数组，数组索引为v3

    invoke-virtual {v0, v1}, Ljava/util/Random;->nextInt(I)I
    move-result v0

    invoke-polymorphic {p1, v0, v1}, Ljava/lang/invoke/MethodHandle;->invoke([Ljava/lang/Object;)Ljava/lang/Object;, (II)V
    invoke-virtual/range {v0 .. v5}, Landroid/location/LocationManager;->requestLocationUpdates(Ljava/lang/String;JFLandroid/location/LocationListener;)V

    add-int v1,v2,v3
    sub-int/2addr v5,v6
    neg-long v6,v7
    int-to-double p8,p9
    add-int/lit16 v0, v1, 12345
    mul-int/lit16 v1, v2,10

    iput-boolean v0, p0, Lcom/disney/xx/XxActivity;->isRunning:Z
    sget-object v0, Lcom/disney/xx/XxActivity;->PREFS_INSTALLATION_ID:Ljava/lang/String;

    if-eqz v2, :cond_c

    packed-switch p1, :pswitch_data_c

    filled-new-array {v0,v1},[I
    filled-new-array/range {v19..v21}, [B
    
    :goto_7
    return-void

    :cond_8
    if-eq v0, v1, :cond_c

    add-int/2addr v1, v1

    goto :goto_7

    :cond_c
    return-void

    :array_18
    .array-data 4
        0x0
        0x1
        0x2
        0x3
        0x4
    .end array-data

    :pswitch_data_c
    .packed-switch 0x0
        :pswitch_6 #case 0
        :pswitch_9 #case 1
    .end packed-switch

.end method
