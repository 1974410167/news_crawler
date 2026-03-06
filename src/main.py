#!/usr/bin/env python3
"""
News Crawler - Main Entry Point

新闻爬虫主程序
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 News Crawler 启动")
    print("=" * 60)
    print()
    print("✅ 环境准备就绪")
    print("📁 项目目录:", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print()
    print("准备就绪，等待指令...")
    print()


if __name__ == "__main__":
    main()
