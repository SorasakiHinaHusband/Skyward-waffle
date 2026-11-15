**简体中文** | [English](README.md)

# 一加 12（waffle）的 Skyward

这是 [Skyward](https://github.com/kirklin/skyward) 0.3.1 在一加 12
（代号 `waffle`，`PJD110`，ColorOS 17 / Android 17）上的移植。代码树包含
[shawude/skyward-oneplus13-sun](https://github.com/shawude/skyward-oneplus13-sun)
里的 OnePlus 兼容改动，并只附带 `waffle` 一个设备的配置。

镜像基于官方 ColorOS 17 `PJD110_17.0.0.100(CN01)` H.11 的 recovery 制作；
测试用的手机后来运行 `PJD110_17.0.1.202(Milk！)`。Skyward 在运行时读取已安装
系统的属性和服务，所以同一镜像对这两个版本都适用。

## 下载

镜像：[**v0.3.1 Release 附件**](https://github.com/SorasakiHinaHusband/Skyward-waffle/releases/download/v0.3.1/skyward-0.3.1-waffle-PJD110_17.0.0.100.img)

```text
SHA-256: 329dbe58f1ba57e79f06941564dea58da9d404018a85a02a44d4d6a1205ac255
```

镜像约 100 MiB，所以作为 Release 附件提供，不直接提交进仓库。制作它所用的
原厂 recovery 也没有提交。

## 已验证

- 能从 recovery 分区启动。
- 显示模式为 `1440x3168x120cmd`（**120 Hz**）。
- 触摸正常；息屏、返回手势正常。
- Wi-Fi 能连接并正常通信（接口可能要等约 70 秒才出现：CNSS 等 modem 的 DMS
  服务超时后回退到默认 MAC）。
- `/data`、`/sdcard` 可挂载，解密正常。
- ADSP 启动后电池图标和电量读数正常。
- 振动正常：触摸点按、返回手势、强度滑块都会振。
- 版本号从 `my_manifest` 读取：`PJD110_17.0.1.202(Milk！)`。

## 刷入

两个 recovery 槽位都刷：

```sh
fastboot flash recovery_a skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot flash recovery_b skyward-0.3.1-waffle-PJD110_17.0.0.100.img
fastboot reboot recovery
```

保留原厂 recovery 以便回滚：

```sh
fastboot flash recovery_a stock-waffle-recovery.img
fastboot flash recovery_b stock-waffle-recovery.img
```

## 构建

打包器会保留原厂内核，只把 recovery 的 ramdisk 换成 Skyward 的。原厂
`recovery.img` 要从 ColorOS 17 `PJD110_17.0.0.100(CN01)` 全量包中取；
`scripts/extract-ota.sh` 和 `tools/ota-extract` 可以在不落盘整个 8.85 GB
包的情况下直接读取 `payload.bin`。

```sh
export ANDROID_NDK_HOME=/path/to/android-ndk-r29
scripts/build.sh waffle stock/waffle/recovery.img out/skyward-0.3.1-waffle-PJD110_17.0.0.100.img
```

## 配置

- `skyward/devices/waffle.toml`：本仓库唯一的设备配置。
- `permissive = true`：让 recovery 在 `kernel` 域下挂载已安装系统的 APEX。
- `[haptics]` 使用 `qcom-hv-haptics`，`t_lra_us` 作为频率回退。
- 单独启动 ADSP 供电池计使用；**故意不启动 MSS**，因为启动它会让这个内核
  卡住，约一分钟后手机复位到 EDL。
- `mtp = false`，不提供文件传输。
- `[wlan]` 使用 `kiwi_v2`、`rfkill` 和两个 CNSS `fs_ready` 开关。

## 目录

```text
skyward/               Skyward 0.3.1 源码 + 本移植的修改
  devices/waffle.toml  设备配置
  crates/              Rust crates
docs/PORTING.md        改了什么、为什么
docs/TESTING.md        首次启动检查清单
patches/               相对上游 Skyward 0.3.1 的补丁
scripts/build.sh       构建 + 打包
scripts/extract-ota.sh
tools/ota-extract/     OTA payload 提取工具
```

## 卡刷包工具

把逐分区移植镜像打成 Skyward 可安装 zip 的独立工具在
[**Skyward-cardzip**](https://github.com/SorasakiHinaHusband/Skyward-cardzip)。
它会先检查每个镜像是否放得进目标分区，写完后再关闭 AVB；不限于一加 12。

## 已知限制

- 不启动蜂窝/modem：启动 `mss` 会把手机复位到 EDL；Wi-Fi 不需要它。
- recovery 里 Wi-Fi 约 70 秒才出现（DMS 超时）。
- MTP/文件传输未启用。
- 原厂 recovery 底包要匹配 `PJD110_17.0.0.100(CN01)` H.11（或兼容的
  ColorOS 17）。

## 许可证

GPL-3.0-or-later，与上游 Skyward 一致。见 `skyward/LICENSE`。
