# SmartScreenOS

中文安装与操作步骤：[使用说明书](docs/USER_GUIDE.zh-CN.md)。

SmartScreenOS 是一个家庭状态展示与控制项目，目标是让旧平板通过浏览器显示家庭信息，并接入 Home Assistant、Dnake MQTT 和 iCloud CalDAV 等服务。作者 Sunny Engineering；项目原创代码采用 Apache License 2.0。

此社区版本从虚构演示配置开始，不包含维护者的家庭配置、照片、凭据、NAS 部署工具、备份或原私有仓库历史。

## 本地演示

需要 Python 3.11 或 3.13：

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock
python tools/run_demo.py
```

打开 http://127.0.0.1:8080 。默认仅监听本机，使用虚构的两房间配置，不连接真实设备，日历关闭。演示数据保存在临时目录，退出后删除。启动器拒绝本进程的出站 socket 操作；这不是操作系统级隔离。不要将没有访问认证的演示服务暴露到互联网。

linux/amd64 Docker 构建、演示 HTTP 接口及非 root 运行已在维护者 iMac 验证通过；记录见 [验证结果](docs/verification/docker-amd64.json)。可用以下命令启动本机演示：

```sh
docker compose -f compose.demo.yaml up --build
```

## 接入自己的家庭

通用适配器代码保留，但本候选版不是自动发现或一键安装产品。每户需要自己的常开主机、网关连接信息、设备映射以及个人服务凭据。相同品牌不代表所有固件和设备都已验证兼容。请将实际配置、数据和凭据放入忽略的 config/local、data、secrets 等本地目录，另行设计实际挂载，不要提交进仓库。

已有家庭控制与 iCloud 的生产验证来自原私有部署；本社区版本完成了离线通用测试、本地演示及 linux/amd64 Docker 构建启动验证，不代表真实家庭接入已重新验证。ARM 镜像和旧 iPad 上的本候选版本尚未验证。

## 测试

```sh
python tools/run_offline_tests.py tests -q
```

保留通用产品测试。针对维护者私有家庭配置的断言、NAS 运维测试和内部部署工具不属于此公开候选版；见 RELEASE_PREPARATION.md。未通过删除通用产品测试来掩盖产品故障。

## 许可证与维护

项目原创代码采用 Apache License 2.0，允许按许可条款使用、修改和商业使用；第三方组件保留各自许可。先阅读 LICENSE、NOTICE、THIRD_PARTY_NOTICES.md 和 SECURITY.md。此目录不包含 Git 历史；不要把原私有仓库历史推入新仓库。

## 复现 Docker 验证（iMac）

安装并启动 Docker Desktop 后，在解压目录运行：

```sh
python3 tools/verify_docker_release.py
```

工具只构建本目录的 linux/amd64 演示镜像，并创建名称随机的临时容器。只绑定本机随机端口；不读 NAS、SSH、生产 Docker 配置或家庭凭据，不挂载主机目录。验证后删除自己创建的临时容器，保留本地镜像。结果位于 `.release-validation/docker-verification.json`，构建日志仅留本机。该工具不推送镜像，也不创建 GitHub 仓库。

把结果 JSON 发给维护者即可，不需要发送日志或任何口令。此工具用于复现验证，不会上传任何文件。
