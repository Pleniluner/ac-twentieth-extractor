# ac-twentieth-extractor

从本机安装的 ASUS 奥创中心（Armoury Crate）中提取 20 周年主题（内部名 `Twentieth`）资源的
小工具。仓库只包含脚本与哈希清单，不包含任何华硕素材。

A small read-only extractor for the activity-limited `Twentieth` theme bundled with ASUS
Armoury Crate. No vendor artwork is hosted here — run the script against your own
installation.

## 为什么要脚本而不是资源包

这套主题没有单独发行，只随客户端安装包提供，活动结束后可能从新版本里消失。素材的著作权归
ASUSTeK COMPUTER INC.，本仓库不转载这些文件，只提供把它们从你自己机器上取出来的方法。

For the same reason there is no download link here: the artwork belongs to ASUSTeK. The
script copies it out of a package you already have installed.

## 用法

```bash
# 看看本机有哪些主题文件（不复制）
python tools/extract_twentieth.py --list

# 导出到 ./extracted
python tools/extract_twentieth.py --out ./extracted

# 指定安装路径（自动探测失败时）
python tools/extract_twentieth.py --package "C:\Program Files\WindowsApps\B9ECED6F.ArmouryCrate_6.7.6.0_x64__qmba6cd70vzyy" --out ./extracted

# 校验导出结果
python tools/extract_twentieth.py --verify ./extracted/manifest.json
```

需要 Windows 与本机已安装的奥创中心。脚本全程只读，不修改 `C:\Program Files\WindowsApps`
下的任何文件。

## 输出

```
extracted/
├── assets/            1363 个文件，按包内原路径存放
├── resources.pri      含主题的 XAML 样式字典
└── manifest.json      每个文件的包内路径、大小、SHA256
```

主题由两部分组成：`resources.pri` 里的样式字典（`ThemeDictionary_Twentieth.xbf`、
`Style_Twentieth.xbf` 等）和各插件的 `Assets/Twentieth` 目录。客户端按上次记录的主题名加载，
日志中可以看到 `Get theme from previous recrod => Twentieth`。

## 参考哈希

`manifest.sha256.txt` 记录了一份 6.7.6.0 的提取结果，1365 行，格式同 `sha256sum`：

```bash
sha256sum -c manifest.sha256.txt
```

用来确认自己提取到的文件与已知版本一致。版本不同则哈希不同，属正常现象。

## 兼容性

在 Armoury Crate 6.7.6.0（包 `B9ECED6F.ArmouryCrate_qmba6cd70vzyy`）上验证通过。
脚本按目录名 `Twentieth` 搜索，只要该主题还在安装包里就能提取；若输出 `no 'Twentieth'
resource folders`，说明这个版本已经不含该主题。

`resources.pri` 与程序版本绑定，不建议跨版本回填，详见脚本内注释与本仓库 Issue。

## 许可

脚本与文档为 MIT，见 [LICENSE](LICENSE)。仓库不含第三方素材。
奥创中心、ROG、TUF Gaming、ASUS 为其各自权利人的商标，本项目与华硕无隶属关系。
