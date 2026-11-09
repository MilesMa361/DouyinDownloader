#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音视频下载器
支持下载无水印抖音视频
"""

import os
import re
import sys
import time
import requests
from urllib.parse import urlparse
import json


class DouyinDownloader:
    """抖音视频下载器类"""
    
    def __init__(self, download_dir="下载"):
        """
        初始化下载器
        
        Args:
            download_dir: 下载文件夹路径
        """
        self.download_dir = download_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 创建下载文件夹
        self._create_download_dir()
    
    def _create_download_dir(self):
        """创建下载文件夹"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            print(f"✓ 已创建下载文件夹: {os.path.abspath(self.download_dir)}")
    
    def extract_video_id(self, url: str) -> str:
        """
        从抖音链接中提取视频ID
        
        Args:
            url: 抖音链接（支持短链接和完整链接）
            
        Returns:
            视频ID
        """
        # 处理短链接，先获取重定向后的真实URL
        if 'v.douyin.com' in url:
            try:
                response = self.session.head(url, allow_redirects=True, timeout=10)
                url = response.url
            except Exception as e:
                raise Exception(f"解析短链接失败: {e}")
        
        # 从URL中提取视频ID
        # 匹配模式: /video/数字 或 /note/数字
        patterns = [
            r'/video/(\d+)',
            r'/note/(\d+)',
            r'modal_id=(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise Exception(f"无法从链接中提取视频ID: {url}")
    
    def get_video_info(self, video_id: str) -> dict:
        """
        获取视频信息
        
        Args:
            video_id: 视频ID
            
        Returns:
            视频信息字典
        """
        # 构造视频详情页面URL
        detail_url = f"https://www.douyin.com/video/{video_id}"
        
        try:
            response = self.session.get(detail_url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"请求视频页面失败: {e}")
        
        # 尝试从页面中提取视频信息
        # 方法1: 查找 RENDER_DATA 或类似的数据
        patterns = [
            r'<script\s+id="RENDER_DATA"\s+type="application/json">(.*?)</script>',
            r'window\._ROUTER_DATA\s*=\s*({.*?})\s*;?\s*</script>',
            r'"playApi"\s*:\s*"(https://.*?)"',
            r'"play_addr".*?"url_list"\s*:\s*\[(.*?)\]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text, re.DOTALL)
            if match:
                try:
                    if 'RENDER_DATA' in pattern:
                        # 解析 RENDER_DATA
                        from urllib.parse import unquote
                        data_str = unquote(match.group(1))
                        data = json.loads(data_str)
                        return self._extract_from_render_data(data, video_id)
                    elif '_ROUTER_DATA' in pattern:
                        # 解析 ROUTER_DATA
                        data = json.loads(match.group(1))
                        return self._extract_from_render_data(data, video_id)
                    else:
                        # 直接匹配到URL
                        video_url = match.group(1).replace('\\u002F', '/')
                        return {
                            'video_id': video_id,
                            'video_url': video_url,
                            'title': f'抖音视频_{video_id}'
                        }
                except Exception as e:
                    continue
        
        # 方法2: 尝试使用API
        return self._get_video_via_api(video_id)
    
    def _extract_from_render_data(self, data: dict, video_id: str) -> dict:
        """从页面数据中提取视频信息"""
        # 递归查找视频信息
        video_url = None
        title = f'抖音视频_{video_id}'
        
        def find_video_url(obj, depth=0):
            nonlocal video_url, title
            if depth > 10 or video_url:
                return
            
            if isinstance(obj, dict):
                # 查找播放地址
                if 'play_addr' in obj:
                    play_addr = obj['play_addr']
                    if isinstance(play_addr, dict) and 'url_list' in play_addr:
                        urls = play_addr['url_list']
                        if urls and isinstance(urls, list):
                            video_url = urls[0]
                            return
                
                if 'playApi' in obj and obj['playApi']:
                    video_url = obj['playApi']
                    return
                
                # 查找标题
                if 'desc' in obj and obj['desc']:
                    title = obj['desc']
                elif 'title' in obj and obj['title']:
                    title = obj['title']
                
                # 继续递归
                for key, value in obj.items():
                    find_video_url(value, depth + 1)
            
            elif isinstance(obj, list):
                for item in obj:
                    find_video_url(item, depth + 1)
        
        find_video_url(data)
        
        if not video_url:
            raise Exception("未能从页面数据中找到视频播放地址")
        
        # 处理URL
        if video_url.startswith('//'):
            video_url = 'https:' + video_url
        
        video_url = video_url.replace('\\u002F', '/')
        
        return {
            'video_id': video_id,
            'video_url': video_url,
            'title': title
        }
    
    def _get_video_via_api(self, video_id: str) -> dict:
        """通过API获取视频信息（备用方法）"""
        api_url = f"https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_id={video_id}"
        
        try:
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'item_list' in data and data['item_list']:
                item = data['item_list'][0]
                video_url = item['video']['play_addr']['url_list'][0]
                title = item.get('desc', f'抖音视频_{video_id}')
                
                # 替换为无水印链接
                video_url = video_url.replace('playwm', 'play')
                
                return {
                    'video_id': video_id,
                    'video_url': video_url,
                    'title': title
                }
        except Exception as e:
            pass
        
        raise Exception(f"获取视频信息失败: 无法找到视频播放地址")
    
    def download_video(self, video_url: str, filename: str) -> str:
        """
        下载视频
        
        Args:
            video_url: 视频URL
            filename: 文件名
            
        Returns:
            保存的文件路径
        """
        # 清理文件名
        filename = self._sanitize_filename(filename)
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        
        file_path = os.path.join(self.download_dir, filename)
        
        # 检查文件是否已存在
        if os.path.exists(file_path):
            print(f"⚠ 文件已存在: {file_path}")
            return file_path
        
        print(f"↓ 开始下载: {filename}")
        
        try:
            response = self.session.get(video_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            # 下载文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 显示下载进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            bar_length = 30
                            filled = int(bar_length * downloaded_size / total_size)
                            bar = '█' * filled + '░' * (bar_length - filled)
                            print(f'\r  进度: [{bar}] {progress:.1f}% ({downloaded_size}/{total_size} bytes)', end='')
                        else:
                            print(f'\r  已下载: {downloaded_size} bytes', end='')
            
            print()  # 换行
            print(f"✓ 下载完成: {file_path}")
            
            return file_path
            
        except Exception as e:
            # 下载失败时删除不完整的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise Exception(f"下载视频失败: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除Windows文件名中的非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        filename = re.sub(illegal_chars, '_', filename)
        
        # 移除控制字符
        filename = ''.join(char for char in filename if ord(char) >= 32)
        
        # 限制文件名长度
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename.strip()
    
    def process_url(self, url: str) -> str:
        """
        处理单个抖音链接
        
        Args:
            url: 抖音链接
            
        Returns:
            下载的文件路径
        """
        print(f"\n{'='*60}")
        print(f"处理链接: {url}")
        print(f"{'='*60}")
        
        # 提取视频ID
        print("1. 提取视频ID...")
        video_id = self.extract_video_id(url)
        print(f"   ✓ 视频ID: {video_id}")
        
        # 获取视频信息
        print("2. 获取视频信息...")
        video_info = self.get_video_info(video_id)
        print(f"   ✓ 标题: {video_info['title']}")
        print(f"   ✓ 视频地址: {video_info['video_url'][:80]}...")
        
        # 下载视频
        print("3. 下载视频...")
        file_path = self.download_video(video_info['video_url'], video_info['title'])
        
        return file_path


def main():
    """主函数"""
    print("="*60)
    print(" "*18 + "抖音视频下载器")
    print("="*60)
    
    # 创建下载器实例
    downloader = DouyinDownloader(download_dir="下载")
    
    # 获取用户输入
    print("\n请输入抖音视频链接（输入 'q' 或 'quit' 退出）:")
    print("支持以下格式:")
    print("  - 短链接: https://v.douyin.com/xxxxx/")
    print("  - 完整链接: https://www.douyin.com/video/xxxxxxxxx")
    print("  - 分享文本: 会自动提取其中的链接")
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            # 退出命令
            if user_input.lower() in ['q', 'quit', 'exit']:
                print("\n感谢使用，再见！")
                break
            
            # 跳过空输入
            if not user_input:
                continue
            
            # 从分享文本中提取链接
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, user_input)
            
            if not urls:
                print("⚠ 未找到有效链接，请重新输入")
                continue
            
            # 处理所有链接
            for url in urls:
                try:
                    downloader.process_url(url)
                except Exception as e:
                    print(f"✗ 处理失败: {e}")
        
        except KeyboardInterrupt:
            print("\n\n程序被中断，再见！")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
