# ClickHouse、InfluxDB、MySQL 综合对比

### 前言
在我的工作场景中，会采集大量工厂设备数据，数据的存储和分析都是用的 InfluxDB，但随着数据规模越来越大，InfluxDB 的性能越来越差，千万级数据的聚合查询很慢，故考虑引入 ClickHouse 分担 InfluxDB 大数据分析的压力，再加上我们业务上也用到了 MySQL ，所以本文的重点是对比 MySQL、InfluxDB、ClickHouse 在六千万数据量下的写入耗时、聚合查询耗时、磁盘占用等各方面性能指标。
### 数据库简介
首先简单介绍一下 MySQL 、InfluxDB、ClickHouse 这3大数据库。
#### MySQL
MySQL 是一个关系型数据库管理系统，由瑞典 MySQL AB 公司开发，属于 Oracle 旗下产品，是最流行的关系型数据库管理系统之一。它所使用的 SQL 语言是用于访问数据库的最常用标准化语言。它采用了双授权政策，分为社区版和商业版，由于其体积小、速度快、总体拥有成本低，尤其是开放源码这一特点，一般中小型和大型网站的开发都选择 MySQL 作为网站数据库。（MySQL 实在是太常用，所以这里就不过多介绍了）
#### InfluxDB
InfluxDB 是一个由 InfluxData 公司开发的开源时序型数据库，专注于海量时序数据的高性能读、高性能写、高效存储与实时分析，在 DB-Engines Ranking 时序型数据库排行榜上位列榜首，广泛应用于DevOps监控、IoT监控、实时分析等场景。
通常来讲按照时间顺序记录系统、设备状态变化的数据被称为时序数据（Time Series Data），如CPU利用率、某一时间的环境温度等。时序数据以时间作为主要的查询纬度，通常会将连续的多个时序数据绘制成线，制作基于时间的多纬度报表，用于揭示数据背后的趋势、规律、异常，进行实时在线预测和预警，时序数据普遍存在于IT基础设施、运维监控系统和物联网中。时序数据主要有以下特点：

- 抵达的数据几乎总是作为新条目被记录，无更新操作；
- 数据通常按照时间顺序抵达；
- 时间是一个主坐标轴。

传统数据库通常记录数据的当前值，时序型数据库则记录所有的历史数据，在处理当前时序数据时又要不断接收新的时序数据，同时时序数据的查询也总是以时间为基础查询条件，并专注于解决以下海量数据场景的问题：

- 时序数据的写入：如何支持千万级/秒数据的写入；
- 时序数据的读取：如何支持千万级/秒数据的聚合和查询；
- 成本敏感：海量数据存储带来的是成本问题，如何更低成本地存储这些数据，是时序型数据库需要解决的关键问题。
#### ClickHouse
ClickHouse 是 Yandex（俄罗斯最大的搜索引擎）开源的一个用于实时数据分析的基于列存储的数据库，其处理数据的速度比传统方法快 100-1000 倍。ClickHouse 的性能超过了目前市场上可比的面向列的 DBMS，每秒钟每台服务器每秒处理数亿至十亿多行和数十千兆字节的数据。ClickHouse 主要有以下特性：

- 快速：ClickHouse 会充分利用所有可用的硬件，以尽可能快地处理每个查询。单个查询的峰值处理性能超过每秒 2 TB（解压缩后，仅使用的列）。在分布式设置中，读取是在健康副本之间自动平衡的，以避免增加延迟。
- 易用：ClickHouse 简单易用，开箱即用。它简化了所有数据处理：将所有结构化数据吸收到系统中，并且立即可用于构建报告。SQL 允许表达期望的结果，而无需涉及某些 DBMS 中可以找到的任何自定义非标准 API。
- 充分利用硬件：ClickHouse 与具有相同的可用 I/O 吞吐量和 CPU 容量的传统的面向行的系统相比，其处理典型的分析查询要快两到三个数量级。列式存储格式允许在 RAM 中容纳更多热数据，从而缩短了响应时间。
- 提高 CPU 效率：向量化查询执行涉及相关的 SIMD 处理器指令和运行时代码生成。处理列中的数据会提高 CPU 行缓存的命中率。
- 优化磁盘访问：ClickHouse 可以最大程度地减少范围查询的次数，从而提高了使用旋转磁盘驱动器的效率，因为它可以保持连续存储数据。
- 最小化数据传输：ClickHouse 使公司无需使用专门针对高性能计算的专用网络即可管理其数据。

ClickHouse 是一个用于联机分析（OLAP）的列式数据库管理系统（DBMS）。

- OLTP：是传统的关系型数据库，主要操作增删改查，强调事务一致性，比如银行系统、电商系统。
- OLAP：是仓库型数据库，主要是读取数据，做复杂数据分析，侧重技术决策支持，提供直观简单的结果。

ClickHouse OLAP 场景的特点：1）读多于写；2）大宽表，读大量行但是少量列，结果集较小；3）数据批量写入，且数据不更新或少更新；4）无需事务，数据一致性要求低；5）灵活多变，不适合预先建模。
### 环境准备
在阿里云买了一台 16c64g 的服务器，操作系统 centos 7.8，使用 sealos 一键安装 k8s，使用 helm 一键安装 mysql（5.7）、influxdb（1.8）、clickhouse（22.3） ，每个应用各分配 4c16g 的资源。helm  charts 大家可以 `git clone [https://github.com/stone0090/clickhouse-test.git](https://github.com/stone0090/clickhouse-test.git)`获取。
```bash
# 下载 sealos
$ wget https://github.com/labring/sealos/releases/download/v4.0.0/sealos_4.0.0_linux_amd64.tar.gz \
&& tar zxvf sealos_4.0.0_linux_amd64.tar.gz sealos && chmod +x sealos && mv sealos /usr/bin

# 初始化一个单节点 Kubernetes
$ sealos run labring/kubernetes:v1.24.0 labring/calico:v3.22.1 --masters [xxx.xxx.xxx.xxx] -p [your-ecs-password]

# 去掉 master 的污点，允许安装应用到 master 和 control-plane
$ kubectl taint nodes --all node-role.kubernetes.io/master-
$ kubectl taint nodes --all node-role.kubernetes.io/control-plane-

# 获取 mysql、influxdb、clickhouse 一键安装 Helm-Charts
$ wget https://github.com/stone0090/clickhouse-test/archive/refs/tags/v1.0.0-beta.tar.gz
$ tar -zxvf v1.0.0-beta.tar.gz

# 安装 Kubernetes 包管理工具 Helm，以及 mysql、influxdb、clickhouse 3大数据库
$ sealos run labring/helm:v3.8.2
$ helm install mysql clickhouse-test-1.0.0-beta/helm-charts/mysql/
$ helm install influxdb clickhouse-test-1.0.0-beta/helm-charts/influxdb/
$ helm install clickhouse clickhouse-test-1.0.0-beta/helm-charts/clickhouse/
```
### 数据导入
直接使用 ClickHouse 官方提供的测试数据 [https://clickhouse.com/docs/zh/getting-started/example-datasets/opensky](https://clickhouse.com/docs/zh/getting-started/example-datasets/opensky)，此数据集中的数据是从完整的 OpenSky 数据集中派生和清理而来的，以说明 COVID-19 新冠肺炎大流行期间空中交通的发展情况。它涵盖了自2019年1月1日以来该网络超过2500名成员看到的所有航班，总数据量有6600w。
```bash
# 在服务器 /home/flightlist 目录执行以下命令，该目录会被挂载到 mysql-pod、influxdb-pod、clickhouse-pod 内
$ wget -O- https://zenodo.org/record/5092942 | grep -oP 'https://zenodo.org/record/5092942/files/flightlist_\d+_\d+\.csv\.gz' | xargs wget

# 批量解压 flightlist.gz 数据
$ for file in flightlist_*.csv.gz; do gzip -d "$file"; done

# 将 csv 处理成 influxdb 导入所需的 txt 格式（此过程大概耗时1小时）
$ python clickhouse-test-1.0.0-beta/helm-charts/influxdb_csv2txt.py
```
#### MySQL
```bash
# 进入 mysql pod
$ kubectl exec -it [influxdb-podname] -- bash

# 连上 mysql 建库、建表
$ mysql -uroot -p123456
$ use test;
$ CREATE TABLE `opensky` (`callsign` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,`number` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,`icao24` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,`registration` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,`typecode` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,`origin` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,`destination` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,`firstseen` datetime DEFAULT NULL,`lastseen` datetime DEFAULT NULL,`day` datetime DEFAULT NULL,`latitude_1` double DEFAULT NULL,`longitude_1` double DEFAULT NULL,`altitude_1` double DEFAULT NULL,`latitude_2` double DEFAULT NULL,`longitude_2` double DEFAULT NULL,`altitude_2` double DEFAULT NULL,KEY `idx_callsign` (`callsign`),KEY `idx_origin` (`origin`),KEY `idx_destination` (`destination`)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

# 导入数据（大概耗时70分钟）
$ load data local infile 'flightlist_20190101_20190131.csv' into table opensky character set utf8mb4 fields terminated by ',' lines terminated by '\n' ignore 1 lines;
# 省略其他29条导入命令：load data local infile 'flightlist_*_*.csv' into table opensky character set utf8mb4 fields terminated by ',' lines terminated by '\n' ignore 1 lines;

# 检查数据是否导入成功
$ select count(*) from test.opensky;
```
#### InfluxDB
```bash
# 进入 influxdb pod
$ kubectl exec -it [influxdb-podname] -- bash

# 导入数据（大概耗时90分钟，16点25开始）
$ influx -username 'admin' -password 'admin123456' -import -path=/tmp/flightlist/flightlist_20190101_20190131.txt -precision=ns;
# 省略其他29条导入命令：influx -username 'admin' -password 'admin123456' -import -path=/tmp/flightlist/flightlist_*_*.txt -precision=ns;

# 检查数据是否导入成功
$ influx -username 'admin' -password 'admin123456'
$ select count(latitude_1) from test.autogen.opensky;
```
#### ClickHouse
```bash
# 进入 clickhouse pod
$ kubectl exec -it [clickhouse-podname] -- bash

# 连上 clickhouse 建库、建表
$ clickhouse-client
$ create database test;
$ use test;
$ CREATE TABLE opensky(callsign String,number String,icao24 String,registration String,typecode String,origin String,destination String,firstseen DateTime,lastseen DateTime,day DateTime,latitude_1 Float64,longitude_1 Float64,altitude_1 Float64,latitude_2 Float64,longitude_2 Float64,altitude_2 Float64) ENGINE = MergeTree ORDER BY (origin, destination, callsign);
$ exit

# 导入数据（大概耗时75秒）
$ cd /tmp/flightlist
$ for file in flightlist_*.csv; do cat "$file" | clickhouse-client --date_time_input_format best_effort --query "INSERT INTO test.opensky FORMAT CSVWithNames"; done

# 检查数据是否导入成功
$ clickhouse-client
$ SELECT count() FROM test.opensky;
```
### 测试场景
#### MySQL
```plsql
$ mysql -uroot -p123456
$ use test;
-- 开启性能分析
set profiling = 1;
-- 查询磁盘空间
select table_rows as `总行数`, (data_length + index_length)/1024/1024/1024 as `磁盘占用(G)` from information_schema.`TABLES` where table_name = 'opensky';
-- 全表count
select count(latitude_1) from opensky;
-- 全表max/min
select max(longitude_1),min(altitude_1) from opensky;
-- 全表平均值
select avg(latitude_2) from opensky;
-- 全表方差
select var_pop(longitude_2) from opensky;
-- 复杂查询1：全表多个字段聚合查询
select count(latitude_1),max(longitude_1),min(altitude_1),avg(latitude_2) from opensky;
-- 复杂查询2：从莫斯科三个主要机场起飞的航班数量
SELECT origin, count(1) AS c FROM opensky WHERE origin IN ('UUEE', 'UUDD', 'UUWW') GROUP BY origin;
-- 输出分析结果
show profiles;
```
#### InfluxDB
```plsql
$ influx -username 'admin' -password 'admin123456'
$ use test;
-- 耗时统计，queryReqDurationNs 是累计查询时间，2次任务的时间相减就是耗时
select queryReq,queryReqDurationNs/1000/1000,queryRespBytes from _internal."monitor".httpd order by time desc limit 10;
-- 查询磁盘空间
select sum(diskBytes) / 1024 / 1024 /1024 from _internal."monitor"."shard" where time > now() - 10s group by "database";
-- 全表count
select count(latitude_1) from opensky;
-- 全表max/min
select max(longitude_1),min(altitude_1) from opensky;
-- 全表平均值
select mean(latitude_2) from opensky;
-- 全表方差
select stddev(longitude_2) from opensky;
-- 复杂查询1：全表多个字段聚合查询
select count(latitude_1),max(longitude_1),min(altitude_1),mean(latitude_2) from opensky;
-- 复杂查询2：从莫斯科三个主要机场起飞的航班数量
SELECT count(latitude_1) AS c FROM opensky WHERE origin =~/^UUEE|UUDD|UUWW$/ GROUP BY origin;
```
#### ClickHouse
```plsql
$ clickhouse-client
$ use test;
-- 耗时统计
select event_time_microseconds,query_duration_ms,read_rows,result_rows,memory_usage,query from system.query_log where query like '%opensky%' and query_duration_ms <> 0 and query not like '%event_time_microseconds%' order by event_time_microseconds desc limit 5;
-- 查询磁盘空间
SELECT formatReadableSize(total_bytes) FROM system.tables WHERE name = 'opensky';
-- 全表count
select count(latitude_1) from opensky;
-- 全表max/min
select max(longitude_1),min(altitude_1) from opensky;
-- 全表平均值
select avg(latitude_2) from opensky;
-- 全表方差
select var_pop(longitude_2) from opensky;
-- 复杂查询1：全表多个字段聚合查询
select count(latitude_1),max(longitude_1),min(altitude_1),avg(latitude_2) from opensky;
-- 复杂查询2：从莫斯科三个主要机场起飞的航班数量
SELECT origin, count() AS c FROM opensky WHERE origin IN ('UUEE', 'UUDD', 'UUWW') GROUP BY origin;
```
### 测试结论
为了确保测试结果相对准确，每条sql起码执行5次取中间值，验证结果如下表格所示：

| 
 | MySQL | InfluxDB | ClickHouse |
| --- | --- | --- | --- |
| 导入耗时 | 大概耗时70分钟 | 大概耗时35分钟 | 75秒 |
| 磁盘空间 | 12.35 G | 5.9 G | 2.66 G |
| 全表count | 24366 ms | 11674 ms | 100 ms |
| 全表max/min | 27023 ms | 26829 ms | 186 ms |
| 全表平均值 | 24841 ms | 12043 ms | 123 ms |
| 全表方差 | 24600 ms | OOM | 113 ms |
| 复杂查询1 | 30260 ms | OOM | 385 ms |
| 复杂查询2 | 470 ms | 200 ms | 8 ms |

最终的结论是，在 6600w 数据量下，ClickHouse 无论是导入速度、磁盘占用、查询性能都完全碾压 MySQL 和 InfluxDB，其中 InfluxDB 表现比想象中的要差，甚至还不如 MySQL，也有可能是我的数据样本和测试用例并不适合 InfluxDB 场景导致的，大家如果对测试结果有疑问，可以自行 `git clone [https://github.com/stone0090/clickhouse-test.git](https://github.com/stone0090/clickhouse-test.git)`项目完整体验以上对比过程。
### 参考引用

- [InfluxDB与MySQL的性能测试 - 走看看](http://t.zoukankan.com/juanxincai-p-14736218.html)
- [识堂 | 笔记分享讨论社区，让知识说话](https://www.yinxiang.com/everhub/note/d134fecc-b51a-4a6b-a3d2-cff6f903bb7d)
- [InfluxDB优化配置项_sqtce的技术博客_51CTO博客](https://blog.51cto.com/u_536410/5399323)
- [influxDB系列（二）--查看数据库的大小 - 立志做一个好的程序员 - 博客园](https://www.cnblogs.com/oxspirt/p/7132235.html)
- [InfluxDB与MySQL的性能测试 - 卷心菜的奇妙历险 - 博客园](https://www.cnblogs.com/juanxincai/p/14736218.html)
- [ClickHouse 基础介绍 - 走看看](http://t.zoukankan.com/VicLiu-p-15661858.html)
- [Clickhouse技术分享_大数据_scalad_InfoQ写作社区](https://xie.infoq.cn/article/e6e2658fe7d512f0d2f5b3325?source=app_share)
- [Hologres vs Clickhouse性能对比参考测试 - 实时数仓Hologres - 阿里云](https://help.aliyun.com/document_detail/300377.html?spm=5176.12818093.help.dexternal.3be916d0aK7NfW&scm=20140722.S_help%40%40%E6%96%87%E6%A1%A3%40%40300377.S_hot%2Bos0.ID_300377-RL_clickhouse%20%E6%80%A7%E8%83%BD%E6%B5%8B%E8%AF%95-LOC_consoleUNDhelp-OR_ser-V_2-P0_1)
