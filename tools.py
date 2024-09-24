import sys  # 导入 sys 模块,用于与 Python 解释器进行交互
import re  # 导入 re 模块,用于正则表达式匹配
import time  # 导入 time 模块,用于获取当前时间和计时
import subprocess  # 导入 subprocess 模块,用于执行系统命令
import dns.resolver  # 导入 dns.resolver 模块,用于进行 DNS 查询
from urllib.parse import urlsplit, urlunsplit  # 从 urllib.parse 模块导入 urlsplit 和 urlunsplit 函数,用于处理 URL

def get_pop_ip(cf_subdomain, pop):
    """
    使用 DNS 查询获取指定 CloudFront 子域名和 POP ID 的 IP 地址列表。
    :param cf_subdomain: CloudFront 子域名
    :param pop: POP ID
    :return: IP 地址列表
    """
    ips = []
    domain_name = '{}.{}.cloudfront.net'.format(cf_subdomain, pop)
    try:
        response = dns.resolver.resolve(domain_name, 'A')
        for rdata in response:
            ips.append(rdata.address)
    except dns.resolver.NoAnswer:
        return ips
    return ips

def get_ip(ips, ip_index):
    """
    从 IP 地址列表中获取指定索引位置的 IP 地址。
    :param ips: IP 地址列表
    :param ip_index: IP 地址索引
    :return: 指定索引位置的 IP 地址
    """
    if (len(ips) > ip_index):
        return ips[ip_index]
    else:
        return ips[ip_index-len(ips)]

def download_file_with_curl(url, ips, header, index_retry):
    """
    使用 curl 命令下载指定 URL 的文件,并返回 CloudFront 相关信息。
    :param url: 要下载的 URL
    :param ips: IP 地址列表
    :param header: HTTP 请求头
    :param index_retry: IP 地址索引,用于重试
    :return: 包含命令、CloudFront 请求 ID、POP 等信息的字典
    """
    result = {}
    try:
        ip = get_ip(ips, index_retry)
        parsed_url = urlsplit(url)
        domain = parsed_url.netloc

        local_filename = '/dev/null'  # 将文件下载到 /dev/null,不保存文件内容

        command = []
        header_command = []

        for header_item in header:
            header_command.extend(['-H', header_item])

        command = [
            'curl',
            '-D',
            '-',  # 将响应头输出到标准输出
            '--connect-timeout',
            '6',
            url,
            '--resolve',
            f'{domain}:443:{ip}',  # 指定 IP 地址用于解析域名
            '-o',
            local_filename
        ]
        command.extend(header_command)

        run_result = subprocess.run(command, text=True,
                                    capture_output=True, encoding='utf-8')

        cf_request_id_group = re.search(
            r'x-amz-cf-id:\s*(.*)', run_result.stdout)
        cf_request_pop_group = re.search(
            r'x-amz-cf-pop:\s*(.*)', run_result.stdout)

        std_error = run_result.stderr.splitlines()
        result['stderr'] = std_error[len(std_error)-1]

        if cf_request_id_group:
            result['cf_request_id'] = cf_request_id_group.group(1)

        if cf_request_pop_group:
            result['cf_request_pop'] = cf_request_pop_group.group(1)

        result['command'] = ' '.join(command)
        result['local_filename'] = local_filename

        # 使用正则表达式匹配响应头中的 x-cache、x-amz-cf-pop 和 age
        x_cache_match = re.search(r'x-cache:\s*(.*)', run_result.stdout, re.IGNORECASE)
        age_match = re.search(r'age:\s*(.*)', run_result.stdout, re.IGNORECASE)

        if x_cache_match:
            x_cache_value = x_cache_match.group(1)
            result['x-cache'] = x_cache_value

        if age_match:
            age_value = age_match.group(1)
            result['age']=age_value
            
    except Exception as e:
        raise Exception(
            f'Failed to download file with curl command:{" ".join(command)}, exception: {e}')
    return result

if __name__ == "__main__":
    cf_domain = 'xxx' # 使用您的Distribution domain name替换，{cf_domain}.cloudfront.net
    headers = ["Accept-Encoding=gzip,br,deflate"]

    # 读取 URL 和 POP ID 文件
    with open('urls.txt', 'r') as f:
        urls = f.read().splitlines()

    with open('pop_ids.txt', 'r') as f:
        pop_ids = f.read().splitlines()

    # 遍历 URL 和 POP ID
    for url in urls:
        for pop_id in pop_ids:
            index_retry = 0
            pop_ips = get_pop_ip(cf_domain, pop_id)
            while index_retry < 3:
                start_time = time.time()
                try:
                    curl_result = download_file_with_curl(
                        url, pop_ips, headers, index_retry)
                    end_time = time.time()
                    execution_time = end_time - start_time
                    command = curl_result.get('command', 'no command')
                    cf_request_id = curl_result.get('cf_request_id', '')
                    cf_request_pop = curl_result.get('cf_request_pop', '')
                    x_cache = curl_result['x-cache']
                    age = curl_result['age']

                    print(f"URL: {url}")
                    print(f"POP ID: {pop_id}")
                    # print(f"Command: {command}")
                    # print(f"CF Request ID: {cf_request_id}")
                    print(f"CF Request POP: {cf_request_pop}")
                    print(f"X-Cache: {x_cache}")
                    print(f"Age: {age}")
                    print(f"Execution time: {execution_time:.6f} seconds")
                    break
                except Exception as e:
                    error_message = str(e)
                    print(error_message)

                index_retry += 1
            