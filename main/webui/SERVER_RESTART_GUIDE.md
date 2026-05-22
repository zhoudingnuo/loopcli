# WebUI 服务器重启指南

## 当前状态
- Health API代码已添加到server.py
- 需要8080端口的所有进程重启才能生效
- 当前有多个进程占用8080端口

## 重启步骤

### 1. 查找占用8080端口的进程
```bash
netstat -ano | grep 8080 | grep LISTENING
```

### 2. 安全终止进程
```bash
# 获取所有PID
PIDS=$(netstat -ano | grep 8080 | grep LISTENING | awk '{print $5}' | sort -u)

# 逐个终止
for pid in $PIDS; do
    echo "终止进程 $pid"
    kill $pid
done

# 等待端口释放
sleep 5
```

### 3. 确认端口已释放
```bash
netstat -ano | grep 8080 | grep LISTENING
# 应该没有输出
```

### 4. 启动新的WebUI服务器
```bash
cd D:/loopcli/main/webui
python server.py
```

### 5. 验证Health API
```bash
curl http://localhost:8080/api/health
# 应该返回JSON格式的健康状态
```

## 注意事项
- 重启会导致短暂的WebUI服务中断（约5-10秒）
- 确保没有正在进行的重要操作
- 建议在低峰期执行重启
- 重启后需要重新登录（如果有的话）

## 新功能
重启后将启用以下新功能：
- `/api/health` - 健康检查端点
  - 系统信息（CPU、内存、磁盘）
  - Agent状态
  - WebUI运行时间
  - 日志信息

## 回滚
如果重启后出现问题，可以：
1. 检查server.py语法：`python -m py_compile server.py`
2. 查看错误日志：`cat D:/loopcli/main/webui/server.log`
3. 恢复之前的版本：`git checkout server.py`
