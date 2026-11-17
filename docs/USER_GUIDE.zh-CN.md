# SmartScreenOS 使用说明书

社区版中文指南　版本 1.0　2026 年 11 月 17 日

作者 Sunny Engineering　项目原创代码许可 Apache License 2.0

本说明书面向希望在常开电脑或 NAS 上运行 SmartScreenOS，并用平板浏览器查看家庭信息的业主。当前公开版先提供不连接真实设备的演示环境；接入自己的 Dnake、Home Assistant 或 iCloud 时，需要另行配置。先完成演示，再进行真实家庭接入。

## 1 使用范围与准备条件

项目地址：https://github.com/Chat202307/SmartScreenOS-Community

主机负责运行服务，平板只是显示和操作终端。日常使用时主机必须保持开机、联网且不进入睡眠；关闭平板不会停止主机服务。已有且支持容器的 NAS 适合长期运行，不要求业主再购买 NAS。

| 项目 | 要求或建议 |
|---|---|
| 主机 | 支持 Docker 的 NAS、电脑或小主机；本版已验证 linux/amd64 演示镜像 |
| 运行资源 | 演示建议从 2 核及 4 GB 内存的主机起步，预留约 10 GB 磁盘预算；这是规划建议，不是实测最低配置；同时运行 HA 等服务应另留资源 |
| 显示终端 | 可打开网页的平板或电脑；旧 iPad 使用 Safari，不要求安装 HA App |
| 网络 | 主机与显示终端位于可互访的家庭网络；iCloud 接入另需访问 Apple 服务的互联网连接 |
| 家庭接入 | 具备本户设备映射、网关或 MQTT 信息；使用 HA 时还需本户 HA 服务及访问令牌 |

同小区 Dnake 设备型号相同，可以复用配置结构，但各户地址、主题、账号、设备标识仍须核对。不得直接套用邻居的凭据，也不得连接小区公共控制系统。

演示环境不提供真实控制、日历登录或持久化家庭数据；退出演示后，临时照片与待办数据会删除。下面的安装命令均在项目根目录运行，该目录中应能看到 README.md、Dockerfile、tools 和 src。

## 2 使用 Docker 启动演示

### 2.1 下载源码与进入目录

在项目页面选择 Code，再选 Download ZIP；解压后进入最外层项目文件夹。GitHub 下载目录可能叫 SmartScreenOS-Community-main，候选包目录可能叫 SmartScreenOS-OpenSource-Candidate，名称不同不影响运行。

Mac 用户打开终端，输入 cd 后加一个普通空格，再把解压文件夹拖进终端，最后按回车。cd 和路径必须在同一行。执行下面命令确认位置：

```sh
pwd
ls
```

### 2.2 启动与访问

电脑上先安装并启动官方 Docker Desktop；NAS 使用厂商提供且支持 Docker Compose 的容器环境。本指南不要求改变 NAS 存储池、共享目录权限或现有生产容器。Mac 安装参考 Docker 官方文档，见第 8 节。

```sh
docker version
docker compose version
docker compose -f compose.demo.yaml up --build -d
```

首次启动需要下载基础镜像和依赖。完成后，在同一台主机的浏览器打开 http://127.0.0.1:8080 。看到页面即可；没有真实设备状态或日历属于演示的正常表现。

```sh
# 查看状态与最近日志
docker compose -f compose.demo.yaml ps
docker compose -f compose.demo.yaml logs --tail=100 demo

# 停止演示并移除本演示容器
docker compose -f compose.demo.yaml down
```

compose.demo.yaml 默认只绑定主机本地回环地址。不要把这套演示 Compose 当作 NAS 正式部署模板。若 8080 端口已被占用，可把该文件的端口行改为 "127.0.0.1:18080:8080"，重新启动后访问 http://127.0.0.1:18080 。不要停止占用端口的其他家庭服务。

如需复现已经完成的发布验证，可运行 python3 tools/verify_docker_release.py；普通使用无需重复执行。该工具会启动后清理自己的临时容器，不会留下长期运行的服务。

## 3 使用 Python 演示与平板访问

### 3.1 原生 Python 演示

不使用 Docker 时，在独立项目目录中准备 Python 3.11 或 3.13。本次社区版离线测试运行于 Python 3.13；Python 3.11 和其他平台仍需在使用环境确认。Mac 应先确认 python3 --version，不要在项目中依赖旧版系统 Python。

```sh
python3 --version
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock
python tools/run_demo.py
```

浏览器打开 http://127.0.0.1:8080 。终端会保持运行，按 Control 与 C 结束；关闭终端也会结束前台服务。以后再次使用，只需进入目录、激活 .venv，再运行最后一行。Windows PowerShell 的激活命令是 .\.venv\Scripts\Activate.ps1，其余步骤需按本机 Python 命令调整。

### 3.2 在同一家庭网络的 iPad 打开演示

默认的 127.0.0.1 只允许主机自己访问。若要在平板查看演示，先停止原生演示，再运行下面命令。此操作仅在受信任的家庭局域网进行：

```sh
python tools/run_demo.py --host 0.0.0.0 --port 8080
```

在主机网络设置中查找其局域网地址。假设演示地址是 192.0.2.10，则平板 Safari 输入 http://192.0.2.10:8080 。此地址仅为文档示例，必须替换为自家主机的真实局域网地址。不要在平板输入 127.0.0.1 或 0.0.0.0。

若无法访问，先确认主机能打开本地页面，再检查平板与主机是否互通、是否处于访客 Wi-Fi，以及主机防火墙是否允许家庭网络访问该端口。无需为了调试关闭整个防火墙。

可以在 Safari 使用添加到主屏幕，方便下次打开。先确认实际显示和触控正常；本社区构建尚未重新验证旧 iPad 的所有 Safari 版本。不要配置公网端口转发，演示网页不具备面向公网的访问认证。

## 4 接入自己的家庭设备

### 4.1 演示与真实服务的区别

run_demo.py 会清除继承的集成环境变量，并拒绝本进程出站网络连接。因此给演示容器填写 HA、MQTT 或 iCloud 密码，不会把它变成真实家庭系统。真实接入需要维护者准备单独的启动和挂载配置，使用实际应用入口，而不是继续修改演示入口。

| 接入方向 | 每户需准备的信息 |
|---|---|
| Home Assistant | 本户 HA 地址、访问令牌、实际实体 ID 和允许控制的设备范围 |
| Dnake MQTT | 本户可访问的 broker 地址与端口、必要的账号认证、状态与控制主题及设备对应关系 |
| 米家设备 | 已在本户环境验证可用的 HA 或其他适配器接入；不能保证任意扫地机、净化器均即插即用 |
| iCloud 日历 | 本户 Apple 账号、单独生成的应用专用密码与需要显示的日历范围 |

源码中已有的 HA 环境变量为 SMARTSCREEN_HA_URL 与 SMARTSCREEN_HA_TOKEN；Dnake MQTT 使用 SMARTSCREEN_DNAKE_MQTT_HOST、SMARTSCREEN_DNAKE_MQTT_PORT、SMARTSCREEN_DNAKE_MQTT_USERNAME 和 SMARTSCREEN_DNAKE_MQTT_PASSWORD。MQTT 用户名与密码须成对提供。环境变量名称可以公开，实际值仅在本机设置。

### 4.2 配置文件职责

配置入口默认位于 config 目录。home.json 定义区域和房间；device_data.json 定义设备、适配器、状态与控制；home_entities.json 与 platform_entities.json 保存实体映射。

dashboard_presentation.json 定义展示分组；household_actions.json 定义场景动作；calendar.json 或自定义日历文件定义日历来源和凭据引用。修改展示分组不会自动建立设备接入，场景中的设备引用也必须与真实映射一致。

不要仅凭设备名称猜测实体，也不要整户复制其他业主的设备清单。先确认设备读状态正确，再在本人同意且有人在场时试单个控制。门锁、报警和其他敏感设备不应被当作普通灯光测试。

config/local、data 和 secrets 是本地文件存放约定，不代表程序自动加载这些目录。当前命令行没有 --device-data-file 等完整家庭配置参数；实际设备接入需维护者提供启动封装，不能照搬不存在的选项。所有挂载与路径应显式指定，避免读写已有生产数据。

## 5 准备 iCloud 日历凭据

以下是 Mac 或 Linux 原生 Python 的独立日历试用步骤，要求先完成第 3 节的虚拟环境安装；不用于替换已有生产服务，也不适用于直接往演示 Docker 中填写凭据。

### 5.1 生成应用专用密码

本人登录 https://account.apple.com ，在登录与安全中进入应用专用密码，生成一个供 SmartScreenOS 使用的密码。Apple 要求账号已启用双重认证。这里需要的是应用专用密码，不是 Apple 主密码、短信验证码或手机解锁密码。

### 5.2 在本机私下保存凭据

在项目根目录执行下面完整代码块。输入过程不回显，内容不会写进 shell 命令历史。文件保存在本机 secrets 目录，不要上传或分享。若同名文件已存在，代码会停止，避免覆盖已有凭据。

```sh
python - <<'PY'
from pathlib import Path
from getpass import getpass
import os

directory = Path("secrets")
directory.mkdir(mode=0o700, exist_ok=True)
directory.chmod(0o700)
files = [directory / "icloud-user.txt",
         directory / "icloud-password.txt"]
if any(path.exists() for path in files):
    raise SystemExit("文件已存在，请保留原文件，不自动覆盖")
values = [getpass("Apple 账号（不回显）: ").strip(),
          getpass("应用专用密码（不回显）: ").strip()]
if not all(values):
    raise SystemExit("内容不能为空，未写入文件")
for path, value in zip(files, values):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT |
                 os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(value + "\n")
print("凭据已写入本机文件，未显示内容")
PY
```

这是 Unix 文件权限示例，不适用于直接调整 NAS 生产权限。不要递归 chmod，不要把其他目录改为 777。首次输入错误时先停止试用，由本人私下更正本机凭据文件；不要把文件内容或终端密码截图发到公开 issue。

## 6 配置与启动独立日历试用

### 6.1 保存日历配置

建立 config/local 目录，在其中新建 calendar.json，保存为下面的 JSON。该文件只引用凭据位置，不包含账号或密码本身。

```json
{
  "schema_version": 1,
  "enabled": true,
  "provider": "caldav",
  "url": "https://caldav.icloud.com/",
  "calendar_id": null,
  "timezone": "Asia/Shanghai",
  "timeout_seconds": 30,
  "refresh_timeout_seconds": 120,
  "allow_stale": false,
  "username_file_env": "SMARTSCREEN_ICLOUD_USERNAME_FILE",
  "password_file_env": "SMARTSCREEN_ICLOUD_PASSWORD_FILE"
}
```

calendar_id 为 null 时发现并读取账号可访问的日历；指定单个日历时使用服务返回的准确 URL 标识，不是日历显示名称。当前一份配置对应一个 Apple 账号，没有多账号配置界面。

### 6.2 使用独立端口启动

以下命令使用 18080 端口与本地试用数据，避免与 8080 演示冲突。请在新开且未设置家庭控制集成环境变量的终端中执行，并先激活 .venv；否则实际应用可能启用已有的 HA 或 MQTT 配置。

```sh
mkdir -p config/local data/calendar-trial/photos
export SMARTSCREEN_ICLOUD_USERNAME_FILE="$PWD/secrets/icloud-user.txt"
export SMARTSCREEN_ICLOUD_PASSWORD_FILE="$PWD/secrets/icloud-password.txt"
python -m src.smartscreen_display.application \
  --config config/runtime.yaml \
  --host 127.0.0.1 --port 18080 \
  --home-file config/demo_home_status.json \
  --photo-dir data/calendar-trial/photos \
  --todo-file data/calendar-trial/todos.json \
  --calendar-config-file config/local/calendar.json
```

打开 http://127.0.0.1:18080 ，等待首次读取后查看家庭日历。修改、增加或删除日程应在 Apple 日历中完成；此接入按只读方式获取日历，不提供向 Apple 写入日程的功能。按 Control 与 C 停止服务，本节 data 目录的数据会保留。

本节是依据现有源码参数整理的原生试用方法，未单独在每种业主环境验证。正式 NAS 的只读凭据挂载、UID/GID、数据持久化及自动重启需另行部署，不能用临时试用步骤直接替换生产容器。

## 7 日常使用与常见问题

### 7.1 看日历与设备状态

首页日历可展开查看未来 10 天。新增事件后未立即显示，不一定是认证失败；源码包含约 300 秒的日历缓存，后台刷新和网络耗时还会影响更新时间。refresh_timeout_seconds 是一次刷新的时间预算，不是每隔多少秒刷新。浏览器刷新也不保证跳过服务端缓存。

日历更新中表示后台正在读取。先等待一个缓存周期，再对照 Apple 日历中的事件日期、时区、所选日历及账号。若长时间不恢复，再看日志。家庭设备无状态通常与接入映射或连接有关，不能通过反复发送物理控制命令来验证服务是否存活。

| 现象 | 先检查什么 |
|---|---|
| permission denied 后面跟文件夹路径 | 是否只输入了文件夹路径；应使用 cd 加空格和路径，放在同一行；不需要改目录权限 |
| cannot open tools/verify_docker_release.py | 当前不在项目根目录，或下载了旧版候选包；用 pwd 与 ls 确认 |
| Cannot connect to Docker daemon | Docker Desktop 或 NAS 容器服务是否已启动；不要为了连通而改用生产 Docker 主机 |
| 端口已占用 | 改用未占用的本地端口，不停止其他服务；Docker 改映射的左侧主机端口 |
| 平板无法打开网页 | 是否仍绑定 127.0.0.1；平板和主机是否能互访；是否连接访客 Wi-Fi |
| iCloud HTTP 401 | Apple 账号是否正确、凭据文件能否读取、是否使用有效应用专用密码；不要打印凭据 |
| 日历为空 | 是否仍在演示模式；事件是否位于未来 10 天；账号、日历筛选和时区是否一致 |
| 控制按钮无效 | 演示模式不会控制设备；真实模式需核对适配器、主题、实体 ID 和服务连接 |

### 7.2 密码失效与异常处理

在 Apple 端撤销应用专用密码，或修改、重置 Apple 主密码，可能导致已保存的应用专用密码失效。由本人重新生成并在本机更新，保留正确的文件读取权限；不要把应用密码写进 compose、镜像或公开配置。

如果正式家庭服务出现影响控制或可用性的异常，停止新版本试用并按本户已经准备好的方案恢复旧服务。当前社区仓库没有通用生产切换和自动回滚工具；演示验证工具的清理功能不等于生产回滚。

## 8 数据维护 隐私与支持

### 8.1 数据保存与升级

演示模式使用临时目录，重启后不保留照片与待办。真实服务必须明确配置持久化目录；数据目录不应放进源码、镜像或公开仓库。备份应覆盖本户配置、数据以及单独保护的凭据，并在独立目录中验证恢复。

更新时先记录当前版本与配置，备份后把新源码放到另一目录，使用独立端口检查，再按本户方案切换。不要覆盖正在使用的数据，不要把整个私有项目上传到公开仓库。原生产版本和可用备份应保留到新版本确认正常。

### 8.2 分享和问题反馈

向邻居分享公开仓库及本说明书即可。GitHub 下载源码不要求填写 HA、Apple 或 MQTT 密码。不要分享真实 config、secrets、照片、日程、完整日志、sealed 文件、口令或生产恢复状态文件。

反馈问题时提供所用提交版本、主机系统与架构、启动方式、错误阶段、HTTP 状态码和去标识化的复现步骤。日志先在本机检查，删除账号、访问令牌、设备地址及日程内容后再提交 issue。没有去标识化把握时只描述现象，不上传日志。

### 8.3 当前验证范围与许可证

本指南对应公开源码基线 92daa813270d。该版通过了离线通用测试，验证工具另通过了独立模拟测试。维护者 iMac 的 linux/amd64 Docker 构建、演示 HTTP 与非 root 运行验证通过，临时容器已清理。

尚未验证 ARM 原生镜像、每种 NAS 图形界面导入、所有旧 iPad Safari、其他业主的真实家庭映射或多 Apple 账号。日历、HA、MQTT 适配器代码存在，不代表所有型号和固件自动兼容。

原创项目代码采用 Apache License 2.0，允许按条款使用、修改和商业使用；保留 LICENSE 与 NOTICE。第三方组件仍按各自许可证使用，具体见 THIRD_PARTY_NOTICES.md。当前只发布源码与构建文件，没有发布公共二进制镜像。

### 8.4 官方参考与项目资料

- 项目与源码：https://github.com/Chat202307/SmartScreenOS-Community
- 发布验证：仓库 docs/verification/docker-amd64.json 与 VALIDATION.json
- Docker Desktop Mac 安装：https://docs.docker.com/desktop/setup/install/mac-install/
- Apple 应用专用密码：https://support.apple.com/en-us/102654
- Apache License 2.0：https://www.apache.org/licenses/LICENSE-2.0

