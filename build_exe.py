#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将Python项目打包成单个exe文件的脚本
"""

import os
import sys
import subprocess
import shutil

def install_pyinstaller():
    """安装PyInstaller"""
    try:
        import PyInstaller
        print("PyInstaller已安装")
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller安装完成")

def build_executable():
    """构建可执行文件"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(current_dir, "main.py")
    
    if not os.path.exists(main_script):
        print(f"错误: 找不到主脚本 {main_script}")
        return False
    
    # 构建命令 - 添加了数据文件包含选项
    cmd = [
        "pyinstaller",
        "--onefile",  # 单文件模式
        "--name", "湖南水利水电信息检索工具",  # 可执行文件名
        "--icon", "./icon/shuangmian.ico",  # 不使用图标（如果需要图标可以指定ico文件路径）
        "--clean",  # 清理临时文件
        "--noconfirm",  # 不询问确认
        "--distpath", "./dist",  # 输出目录
        "--workpath", "./build",  # 构建目录
        "--specpath", "./build",  # spec文件目录
        # 添加数据文件（将parsers目录打包进exe）
        "--add-data", f"{os.path.join(current_dir, 'parsers')}{os.pathsep}parsers",
        # 添加隐藏导入以解决打包后导入问题
        "--hidden-import", "parsers.base_parser",
        "--hidden-import", "parsers.hnslsdxy_parser",
        "--hidden-import", "parsers.voc_parser",
        main_script
    ]
    
    print("开始构建可执行文件...")
    print(f"命令: {' '.join(cmd)}")
    
    try:
        # 执行构建命令
        result = subprocess.run(cmd, cwd=current_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("构建成功!")
            print("可执行文件位于 dist 目录中")
            return True
        else:
            print("构建失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"构建过程中出现异常: {e}")
        return False

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ["build", "dist"]
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"已清理 {dir_name} 目录")
            except Exception as e:
                print(f"清理 {dir_name} 目录时出错: {e}")

def main():
    print("Python项目打包为exe工具")
    print("=" * 30)
    
    # 安装PyInstaller
    install_pyinstaller()
    
    # 询问是否清理之前的构建
    choice = input("是否清理之前的构建文件? (y/n, 默认为y): ").strip().lower()
    if choice in ["", "y", "yes"]:
        clean_build_dirs()
    
    # 构建可执行文件
    if build_executable():
        print("\n打包完成!")
        print("可执行文件位置: dist/湖南水利水电信息检索工具.exe")
    else:
        print("\n打包失败!")

if __name__ == "__main__":
    main()