#循环访问股票信息接口api,地址https://so.eastmoney.com/news/s?keyword=603777
from time import sleep

import akshare as ak
import os
import re
import pandas as pd
import logging
import socket
import time
from datetime import  timedelta
import re
import certifi
import ssl
import smtplib
import csv
import shutil
import chardet
from email.header import Header
from email.mime.text import MIMEText
from datetime import datetime
from dateutil import parser
logger = logging.getLogger()
"""如果当日有新闻，则发送邮件到邮箱"""
# 配置SMTP服务器
# SMTP_SERVER = 'smtp.139.com'  # 139邮箱SMTP服务器
# SMTP_PORT = 465                     # SSL端口
# SENDER_EMAIL = '15254089945@139.com'  # 发件邮箱
# SENDER_PASSWORD = '7f6a6c6d536c34e7a600'  # 授权码

SMTP_SERVER = 'smtp.qq.com'  # 139邮箱SMTP服务器
SMTP_PORT = 465                     # SSL端口
SENDER_EMAIL = '1658727567@qq.com'  # 发件邮箱
SENDER_PASSWORD = 'kehjabrnwhinbeff'  # 授权码

def check_network_connection(host, port, timeout=10):
    """检查网络连接是否正常"""
    try:
        logger.debug(f"尝试连接到 {host}:{port}...")
        socket.create_connection((host, port), timeout=timeout)
        logger.debug("网络连接正常")
        return True
    except socket.error as e:
        logger.error(f"网络连接失败: {str(e)}")
        print(f"✗ 无法连接到服务器: {str(e)}")
        return False

def send_email(stock_content):
    # 1. 检查网络连接
    print("检查网络连接...")
    if not check_network_connection(SMTP_SERVER, SMTP_PORT):
        print("网络连接失败，请检查防火墙或网络设置")
        logger.error("网络连接失败")
        return False
        
    # 2. 连接SMTP服务器
    print("\n正在连接邮件服务器...")
    logger.info(f"尝试连接到 {SMTP_SERVER}:{SMTP_PORT}")
    
    # 尝试不同的连接方式
    server = None
    max_retries = 3
    retry_delay = 5  # 重试延迟(秒)
    
    for attempt in range(max_retries):
        try:
            # 创建SSL上下文
            context = ssl.create_default_context(cafile=certifi.where())
            context.set_ciphers('DEFAULT@SECLEVEL=1')
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # 尝试连接
            server = smtplib.SMTP_SSL(
                host=SMTP_SERVER, 
                port=SMTP_PORT, 
                context=context,
                timeout=30
            )

            # 启用调试输出
            server.set_debuglevel(1)
            time.sleep(2)
            server.ehlo()

            # 使用配置的密码登录
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("✓ 服务器登录成功\n")
            logger.info("服务器登录成功")
            break

        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"服务器断开连接: {str(e)}")
            if attempt < max_retries - 1:
                print(f"服务器断开连接，将在 {retry_delay} 秒后重试 ({attempt+1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print(f"✗ 多次尝试后服务器连接失败: {str(e)}")
                logger.error("多次尝试后服务器连接失败")
                return False

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"认证失败: {str(e)}")
            print(f"✗ 认证失败: {str(e)}")
            print("请检查配置的邮箱和密码是否正确")
            return False

        except Exception as e:
            logger.exception(f"连接失败: {str(e)}")
            print(f"✗ 连接失败: {str(e)}")
            if attempt < max_retries - 1:
                print(f"将在 {retry_delay} 秒后重试 ({attempt+1}/{max_retries})...")
                time.sleep(retry_delay)
            else:
                print("多次尝试后仍无法连接")
                return False

    if server is None:
        print("无法建立邮件服务器连接")
        logger.error("无法建立邮件服务器连接")
        return False

    RECEIVE_EMAIL = "15254089945@139.com"
    subject = "有新的股票新闻"
    body = """
        <html>
        <head></head>
        <body>
        <h1>股票信息</h1>
        <table>
        <tr>
            <th>股票代码</th>
            <th>新闻标题</th>
            <th>发布时间</th>
            <th>网址</th>
        </tr>
        """
    # 创建邮件内容
    # body = ''
    if not stock_content.empty:
        for index, row in stock_content.iterrows():
            body += f"""
            <tr class="category-header">
                <td colspan="3">{row['keyword']}</td>
                <td colspan="3">{row['news_headline']}</td>
                <td colspan="3">{row['release_time']}</td>
                <td colspan="3"><a href="{row['news_link']}">{row['news_link']}</td>
            </tr>
            """
    # 完成HTML内容
    body += """
        </table>
        <p>发件人：赵松彪</p>
        <p>谢谢！<br></p>
    </body>
    </html>
    """
    # 构建邮件
    msg = MIMEText(body, 'html', 'utf-8')
    msg['From'] = Header(SENDER_EMAIL)
    msg['To'] = Header(RECEIVE_EMAIL)
    msg['Subject'] = Header(subject, 'utf-8')
    
    try:
        # 发送邮件
        server.sendmail(SENDER_EMAIL, RECEIVE_EMAIL.split(';'), msg.as_string())
        logger.info(f"成功发送至: {RECEIVE_EMAIL}")
        print(f"✓ 成功发送至: {RECEIVE_EMAIL}")
        server.quit()
        print("邮件发送成功")
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False

#股票新闻查询
def monitor_stock_news(symbol_data)->pd.DataFrame:
    stock_news_em_df = ak.stock_news_em(symbol_data)
    data_news= {
        "keyword": [],
        "news_headline": [],
        "news_content": [],
        "release_time": [],
        "article_source": [],
        "news_link": []
    }
    data_news = pd.DataFrame(data_news)
    for index, row in stock_news_em_df.iterrows():
        #获取当前时间
        date_now = datetime.now().strftime('%Y-%m-%d')

        date_now_minutes = datetime.now()

        # 计算5分钟前的时间
        three_minutes_ago = date_now_minutes - timedelta(minutes=5)

        #新闻发布时间和当前时间一致，处理当前内容
        # 转换为datetime类型
        row['发布时间']= pd.to_datetime(row['发布时间'])
        if row['发布时间'].strftime("%Y-%m-%d") == date_now:
            if three_minutes_ago < row['发布时间']:
                #创建DataFrame数据
                data_news_frame = {
                    "keyword": row['关键词'],
                    "news_headline": row["新闻标题"],
                    "news_content": row['新闻内容'],
                    "release_time": row['发布时间'],
                    "article_source": row['文章来源'],
                    "news_link": row["新闻链接"]
                }
                data_news_frame = pd.DataFrame(data_news_frame,index=[0])
                data_news = pd.concat([data_news, data_news_frame], ignore_index=True)  # 将新行添加到原始DataFrame
            else:
                continue
    return data_news

if __name__ == "__main__":
    #调用股票信息查询方法
    list_data = ["NVO", "MSFT", "01810", "06936", "01519"]
    n=0
    while True:
        for symbol in list_data:
            data = monitor_stock_news(symbol)
            if data.shape[0] > 1:
                send_email(data)
        sleep(300)
        n +=1
        print(f"运行{n}次")