# CloudFront Prewarm Tool

CloudFront Prewarm Tool 是一个用于预热 CloudFront 边缘缓存的工具。它可以针对特定的 CloudFront 边缘节点发送请求,从而将内容缓存到该边缘节点上,提高后续访问的响应速度。

## 特性

- 支持指定 CloudFront 域名、边缘节点 (POP) 和请求头
- 使用 cURL 发送请求,模拟真实用户访问
- 获取并打印关键响应头信息,如 `X-Cache`、`Age`、`CF-Request-Id` 等
- 自动重试失败的请求

## 使用方法

1. 将 `urls.txt` 和 `pop_ids.txt` 文件放置在与脚本相同的目录下。`urls.txt` 包含要预热的 URL 列表,每行一个 URL。`pop_ids.txt` 包含要预热的 CloudFront 边缘节点 ID 列表,每行一个 POP ID。
2. 在命令行中执行脚本:

```
python cloudfront_prewarm.py
```

3. 脚本会遍历 `urls.txt` 和 `pop_ids.txt` 中的所有组合,对每个组合发送预热请求。

4. 预热请求的关键信息会打印在控制台上,包括:
   - Command: 执行的 cURL 命令
   - CF Request ID: CloudFront 请求 ID
   - CF Request POP: 请求的边缘节点 ID
   - X-Cache: 响应头 `X-Cache` 值
   - Age: 响应头 `Age` 值
   - Execution time: 请求执行时间

## 依赖项

- Python 3.x
- dnspython 库 (用于解析 DNS 记录)

## 注意事项

- 为避免对 CloudFront 服务造成过多负载,请合理控制预热请求的频率和数量。
- 根据需要调整 `headers` 列表,添加或修改请求头。
- 如需修改 cURL 命令的其他选项,请在 `download_file_with_curl` 函数中进行更改。

通过使用 CloudFront Prewarm Tool,你可以更好地控制 CloudFront 边缘缓存状态,提高用户访问体验。如有任何问题或改进建议,欢迎提出issues或pull requests。
