; ModuleID = 'foo.c'
source_filename = "foo.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@.str = private unnamed_addr constant [8 x i8] c"smaller\00", align 1
@.str.1 = private unnamed_addr constant [7 x i8] c"bigger\00", align 1
@life = dso_local constant i8 42, align 1
@.str.2 = private unnamed_addr constant [12 x i8] c"Hello world\00", align 1

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @put(i8* %0) #0 {
  %2 = alloca i8*, align 8
  store i8* %0, i8** %2, align 8
  ret void
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @foo(i16 zeroext %0, i16 zeroext %1) #0 {
  %3 = alloca i16, align 2
  %4 = alloca i16, align 2
  store i16 %0, i16* %3, align 2
  store i16 %1, i16* %4, align 2
  %5 = load i16, i16* %3, align 2
  %6 = zext i16 %5 to i32
  %7 = load i16, i16* %4, align 2
  %8 = zext i16 %7 to i32
  %9 = icmp slt i32 %6, %8
  br i1 %9, label %10, label %11

10:                                               ; preds = %2
  call void @put(i8* getelementptr inbounds ([8 x i8], [8 x i8]* @.str, i64 0, i64 0))
  br label %12

11:                                               ; preds = %2
  call void @put(i8* getelementptr inbounds ([7 x i8], [7 x i8]* @.str.1, i64 0, i64 0))
  br label %12

12:                                               ; preds = %11, %10
  ret void
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @main() #0 {
  %1 = alloca i16, align 2
  %2 = alloca i16, align 2
  store i16 42, i16* %1, align 2
  %3 = load i16, i16* %1, align 2
  %4 = zext i16 %3 to i32
  %5 = mul nsw i32 %4, 3
  %6 = trunc i32 %5 to i16
  store i16 %6, i16* %2, align 2
  call void @put(i8* getelementptr inbounds ([12 x i8], [12 x i8]* @.str.2, i64 0, i64 0))
  %7 = load i16, i16* %2, align 2
  %8 = load i16, i16* %1, align 2
  call void @foo(i16 zeroext %7, i16 zeroext %8)
  ret i32 0
}

attributes #0 = { noinline nounwind optnone uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="all" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"clang version 10.0.0-4ubuntu1 "}
