# -*- coding: utf-8 -*-
"""
真实联网搜索 - 允许自行上网查询资料
具体实现：Bing API优先，DuckDuckGo回退，防SSRF，截断
"""
import os
import re
import httpx
from typing import List, Dict
from urllib.parse import urlparse
import ipaddress

class WebSearchReal:
    """真实联网搜索 - 具体实现"""
    
    def __init__(self):
        self.bing_key = os.getenv("BING_API_KEY")
        self.tavily_key = os.getenv("TAVILY_API_KEY")
        self.timeout = 10
        self.max_content = 5000
    
    def _is_safe_url(self, url: str) -> bool:
        """防SSRF - 禁止内网IP"""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https"]:
                return False
            
            # 禁止内网IP
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # 检查是否是IP
            try:
                ip = ipaddress.ip_address(hostname)
                # 禁止私有IP
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except:
                # 不是IP，是域名，检查常见内网域名
                if hostname.lower() in ["localhost", "127.0.0.1", "0.0.0.0"]:
                    return False
            
            return True
        except:
            return False

    async def search(self, query: str, count: int = 5, fetch_content: bool = False) -> Dict:
        """真实搜索 - 具体实现"""
        # 清理查询，防注入
        query = re.sub(r'[^\w\s\u4e00-\u9fa5\-_.,!?]', ' ', query)[:200]
        
        # 优先 Bing API
        if self.bing_key:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(
                        "https://api.bing.microsoft.com/v7.0/search",
                        headers={"Ocp-Apim-Subscription-Key": self.bing_key},
                        params={"q": query, "count": count, "mkt": "zh-CN"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        results = []
                        for item in data.get("webPages", {}).get("value", [])[:count]:
                            url = item.get("url", "")
                            if self._is_safe_url(url):
                                results.append({
                                    "title": item.get("name", ""),
                                    "url": url,
                                    "snippet": item.get("snippet", "")[:300],
                                    "source": "Bing"
                                })
                        return {
                            "query": query,
                            "results": results,
                            "count": len(results),
                            "source": "Bing API",
                            "real": True
                        }
            except Exception as e:
                print(f"Bing搜索失败: {e}")
        
        # 回退 DuckDuckGo HTML（无需Key）
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # DuckDuckGo html接口
                resp = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                if resp.status_code == 200:
                    # 简单解析，避免 bs4 依赖
                    results = []
                    # 提取标题和链接
                    pattern = r'<a[^>]+class="result__url"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>.*?class="result__snippet"[^>]*>([^<]+)</'
                    matches = re.findall(pattern, resp.text, re.DOTALL)[:count]
                    
                    for url, title, snippet in matches:
                        # DuckDuckGo 链接需解码
                        if url.startswith("/"):
                            continue
                        if self._is_safe_url(url):
                            results.append({
                                "title": title.strip()[:100],
                                "url": url[:200],
                                "snippet": snippet.strip()[:300],
                                "source": "DuckDuckGo"
                            })
                    
                    if results:
                        return {
                            "query": query,
                            "results": results,
                            "count": len(results),
                            "source": "DuckDuckGo HTML",
                            "real": True
                        }
        except Exception as e:
            print(f"DuckDuckGo搜索失败: {e}")
        
        # 最后回退：演示数据，但标记为演示
        demo_results = [
            {"title": f"关于 {query} 的解决方案", "url": "https://example.com/1", "snippet": f"这是关于{query}的详细解释...", "source": "演示"},
            {"title": f"{query} 官方文档", "url": "https://example.com/2", "snippet": "官方文档提供了权威说明...", "source": "演示"},
        ]
        
        return {
            "query": query,
            "results": demo_results[:count],
            "count": len(demo_results[:count]),
            "source": "演示（未配置 BING_API_KEY）",
            "real": False,
            "note": "配置 BING_API_KEY 环境变量可启用真实搜索",
            "install_guide": "export BING_API_KEY=your_key 或在 .env 中配置"
        }

    async def fetch_page(self, url: str) -> Dict:
        """获取网页内容 - 用于验证，防SSRF"""
        if not self._is_safe_url(url):
            return {"error": f"不安全URL，禁止访问: {url}", "url": url}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    follow_redirects=True
                )
                
                if resp.status_code != 200:
                    return {"error": f"HTTP {resp.status_code}", "url": url}
                
                # 简单提取正文，避免 bs4 依赖
                text = resp.text
                # 移除 script, style
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
                # 提取标题
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', text, re.IGNORECASE)
                title = title_match.group(1).strip()[:200] if title_match else ""
                # 去除标签
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()[:self.max_content]
                
                return {
                    "url": url,
                    "title": title,
                    "content": text,
                    "length": len(text),
                    "real": True
                }
        except Exception as e:
            return {"error": f"获取失败: {e}", "url": url}

    def get_config_guide(self) -> Dict:
        return {
            "bing_api": {
                "env": "BING_API_KEY",
                "get_key": "https://www.microsoft.com/en-us/bing/apis/bing-web-search-api",
                "free_tier": "1000次/月",
                "real": True
            },
            "tavily": {
                "env": "TAVILY_API_KEY",
                "get_key": "https://tavily.com",
                "real": True
            },
            "duckduckgo": {
                "env": "无需Key",
                "note": "HTML爬取，不稳定，可能被限流",
                "real": True
            },
            "security": {
                "ssrf_protection": "禁止内网IP 127.0.0.1, 10.x, 192.168.x, 172.16.x",
                "timeout": "10秒",
                "max_content": "5000字符截断",
                "allowed_schemes": "http, https only"
            }
        }

web_search_real = WebSearchReal()
