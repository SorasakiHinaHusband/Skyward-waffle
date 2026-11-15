# 首次测试清单 — waffle

> 以下操作只写 recovery 分区，不会清 data。请确认 bootloader 已解锁，并保留
> 原厂 recovery 以便回滚。

## 刷入

```sh
sha256sum skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot flash recovery_a skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot flash recovery_b skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot reboot recovery
```

首次启动可能需要 30–60 秒（等 data 解密和 key 服务）。

## 检查项

按顺序测，哪一步失败就停在那里：

1. **显示**：首页应正常亮度、无花屏；`dmesg | grep 'skyward: display'`
   应显示 `1440x3168x120cmd`（120 Hz）。
2. **触摸**：点按、滑动应正常；屏幕边缘的返回手势应能触发返回。
3. **adb**：`adb devices` 应看到设备；`adb shell id` 应为 `uid=0(root)`。
4. **data 解密**：如果设置了锁屏密码，在解密页输入；`/data`、`/sdcard`
   应可读写。
5. **Wi-Fi**：打开 WLAN 页面扫描并连接。接口可能要等约 70 秒才出现
   （CNSS 等 DMS 超时后用默认 MAC），之后 `ifconfig wlan0` 应拿到地址。
6. **电池**：状态栏应有电池图标和百分比；ADSP 已由 recovery 启动。
7. **振动**：设置里的触摸振动开关、振动强度滑块应可用；点按、返回手势、
   拖动强度滑块都应振动。
8. **版本号**：设置/关于页应显示 `PJD110_17.0.1.202(Milk！)`，不是
   `CP2A...` 这种 build id。
9. **重启**：`重启到系统` 应回到已安装系统；再 `adb reboot recovery` 应回到
   Skyward。

## 注意

- 不要启动 `mss`（蜂窝 modem）：这个内核上启动它约一分钟内会把手机复位到
  EDL。Wi-Fi 不需要它。
- 文件传输（MTP）未启用。

## 出问题时

```sh
adb shell dmesg | grep 'skyward:'
adb shell logcat -d | tail -200
```

保留 `stock-waffle-recovery.img`，需要时刷回两个 recovery 槽位。
