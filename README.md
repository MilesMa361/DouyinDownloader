# 抖音视频下载器

一个简单的抖音视频下载工具，支持下载无水印抖音视频。

## 功能特点

- ✅ 支持短链接和完整链接
- ✅ 自动提取分享文本中的链接
- ✅ 下载无水印视频
- ✅ 显示下载进度
- ✅ 自动创建下载文件夹
- ✅ 支持批量下载

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 运行程序

```bash
python douyin_downloader.py
```

### 支持的链接格式

1. **短链接**（分享链接）:
   ```
   https://v.douyin.com/xxxxx/
   ```

2. **完整链接**:
   ```
   https://www.douyin.com/video/xxxxxxxxx
   ```

3. **分享文本**（自动提取链接）:
   ```
   7.02 February 2nd, 1:58 PM 邀请你观看抖音直播 https://v.douyin.com/xxxxx/
   ```

### 下载位置

视频默认保存在程序运行目录下的 `下载` 文件夹中。

## 项目结构

```
DouyinDownloader/
├── douyin_downloader.py    # 主程序
├── requirements.txt        # 依赖包
├── README.md              # 说明文档
└── 下载/                  # 下载的视频保存目录（自动创建）
```

## 注意事项

1. 请确保网络连接正常
2. 某些视频可能因版权设置无法下载
3. 下载的视频仅供个人学习使用，请勿用于商业用途
4. 请尊重原作者的知识产权

## 许可证

MIT License
