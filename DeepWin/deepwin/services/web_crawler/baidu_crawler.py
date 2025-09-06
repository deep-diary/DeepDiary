#!/usr/bin/env python
# -*- coding:utf-8 -*-
import argparse
import os
import re
import sys
import urllib
import json
import socket
import urllib.request
import urllib.parse
import urllib.error
# 设置超时
import time

timeout = 5
socket.setdefaulttimeout(timeout)


class BaiduCrawler:
    # 睡眠时长
    __time_sleep = 0.1
    __amount = 0
    __start_amount = 0
    __counter = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0', 'Cookie': ''}
    __per_page = 10

    # 获取图片url内容等
    # t 下载图片时间间隔
    def __init__(self, log_manager=None, config_manager=None, t=0.1):
        self.log_manager = log_manager
        self.config_manager = config_manager
        self.time_sleep = t
        self.save_dir = os.path.join(os.path.dirname(__file__), "../../../output/crawler_images")
        
        # 设置日志
        if self.log_manager:
            self.logger = self.log_manager.get_logger(__name__)
        else:
            # 使用统一的日志管理器，避免重复配置
            from deepwin.data_management.log_manager import LogManager
            log_manager = LogManager()
            self.logger = log_manager.get_logger(__name__)

    # 获取后缀名
    @staticmethod
    def get_suffix(name):
        m = re.search(r'\.[^\.]*$', name)
        if m.group(0) and len(m.group(0)) <= 5:
            return m.group(0)
        else:
            return '.jpeg'

    @staticmethod
    def handle_baidu_cookie(original_cookie, cookies):
        """
        :param string original_cookie:
        :param list cookies:
        :return string:
        """
        if not cookies:
            return original_cookie
        result = original_cookie
        for cookie in cookies:
            result += cookie.split(';')[0] + ';'
        result.rstrip(';')
        return result

    # 保存图片
    def save_image(self, rsp_data, word, save_dir = None):
        save_dir = self.save_dir
        if not os.path.exists(save_dir + "/" + word):
            os.mkdir(save_dir + "/" + word)
        # 判断名字是否重复，获取图片长度
        self.__counter = len(os.listdir(save_dir + "/" + word)) + 1
        for image_info in rsp_data['data']:
            try:
                if 'replaceUrl' not in image_info or len(image_info['replaceUrl']) < 1:
                    continue
                obj_url = image_info['replaceUrl'][0]['ObjUrl']
                thumb_url = image_info['thumbURL']
                url = 'https://image.baidu.com/search/down?tn=download&ipn=dwnl&word=download&ie=utf8&fr=result&url=%s&thumburl=%s' % (urllib.parse.quote(obj_url), urllib.parse.quote(thumb_url))
                time.sleep(self.time_sleep)
                suffix = self.get_suffix(obj_url)
                # 指定UA和referrer，减少403
                opener = urllib.request.build_opener()
                opener.addheaders = [
                    ('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'),
                ]
                urllib.request.install_opener(opener)
                # 保存图片
                filepath = save_dir + "/" + word + "/" + str(self.__counter) + str(suffix)
                urllib.request.urlretrieve(url, filepath)
                if os.path.getsize(filepath) < 5:
                    self.logger.info("下载到了空文件，跳过!")
                    os.unlink(filepath)
                    continue
            except urllib.error.HTTPError as urllib_err:
                self.logger.info(urllib_err)
                continue
            except Exception as err:
                time.sleep(1)
                self.logger.info(err)
                self.logger.info("产生未知错误，放弃保存")
                continue
            else:
                self.logger.info("图片+1,已有" + str(self.__counter) + "张图片")
                self.__counter += 1
        return

    # 开始获取
    def get_images(self, word):
        search = urllib.parse.quote(word)
        # pn int 图片数
        pn = self.__start_amount
        while pn < self.__amount:
            url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%s&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=&hd=&latest=&copyright=&word=%s&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&force=&pn=%s&rn=%d&gsm=1e&1594447993172=' % (search, search, str(pn), self.__per_page)
            # 设置header防403
            try:
                time.sleep(self.time_sleep)
                req = urllib.request.Request(url=url, headers=self.headers)
                page = urllib.request.urlopen(req)
                self.headers['Cookie'] = self.handle_baidu_cookie(self.headers['Cookie'], page.info().get_all('Set-Cookie'))
                rsp = page.read()
                page.close()
            except UnicodeDecodeError as e:
                self.logger.info(e)
                self.logger.info('-----UnicodeDecodeErrorurl:', url)
            except urllib.error.URLError as e:
                self.logger.info(e)
                self.logger.info("-----urlErrorurl:", url)
            except socket.timeout as e:
                self.logger.info(e)
                self.logger.info("-----socket timout:", url)
            else:
                # 解析json
                rsp_data = json.loads(rsp, strict=False)
                if 'data' not in rsp_data:
                    self.logger.info("触发了反爬机制，自动重试！")
                else:
                    self.save_image(rsp_data, word)
                    # 读取下一页
                    self.logger.info("下载下一页")
                    pn += self.__per_page
        self.logger.info("下载任务结束")
        return

    def start(self, word, total_page=1, start_page=1, per_page=10):
        """
        爬虫入口
        :param word: 抓取的关键词
        :param total_page: 需要抓取数据页数 总抓取图片数量为 页数 x per_page
        :param start_page:起始页码
        :param per_page: 每页数量
        :return:
        """
        self.__per_page = per_page
        self.__start_amount = (start_page - 1) * self.__per_page
        self.__amount = total_page * self.__per_page + self.__start_amount
        self.get_images(word)

    def batch_download(self, queries, total_pages=1, save_dir=None):
        """
        批量下载多个关键词的图片
        
        Args:
            queries: 关键词列表或单个关键词字符串
            total_pages: 每个关键词的页数
            save_dir: 基础保存目录（暂时未使用，保持接口兼容）
            
        Returns:
            下载结果统计
        """
        # 如果queries是字符串，转换为列表
        if isinstance(queries, str):
            queries = [queries]
        
        results = {}
        start_time = time.time()
        
        for query in queries:
            self.logger.info(f"🔄 开始处理关键词: {query}")
            
            try:
                # 使用原有的start方法
                self.start(query, total_pages, 1, self.__per_page)
                results[query] = {
                    "status": "success",
                    "pages": total_pages,
                    "expected_images": total_pages * self.__per_page
                }
            except Exception as e:
                self.logger.error(f"处理关键词 {query} 时出错: {e}")
                results[query] = {
                    "status": "error",
                    "error": str(e)
                }
        
        total_time = time.time() - start_time
        results["summary"] = {
            "total_queries": len(queries),
            "total_time": total_time,
            "success_count": sum(1 for r in results.values() if r.get("status") == "success")
        }
        
        return results

    def get_download_stats(self, word, output_dir="../../../output/crawler_images"):
        """
        获取指定关键词的下载统计信息
        
        Args:
            word: 关键词
            output_dir: 输出目录
            
        Returns:
            统计信息字典
        """
        try:
            word_dir = os.path.join(output_dir, word)
            if os.path.exists(word_dir):
                image_count = len([f for f in os.listdir(word_dir) 
                                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
                return {
                    "keyword": word,
                    "image_count": image_count,
                    "directory": word_dir
                }
            else:
                return {
                    "keyword": word,
                    "image_count": 0,
                    "directory": word_dir
                }
        except Exception as e:
            self.logger.error(f"获取下载统计时出错: {e}")
            return {
                "keyword": word,
                "error": str(e)
            }

    def cleanup_empty_files(self, word, output_dir="../../../output/crawler_images"):
        """
        清理指定关键词目录下的空文件
        
        Args:
            word: 关键词
            output_dir: 输出目录
            
        Returns:
            清理结果
        """
        try:
            word_dir = os.path.join(output_dir, word)
            if not os.path.exists(word_dir):
                return {"status": "no_directory", "message": f"目录 {word_dir} 不存在"}
            
            cleaned_count = 0
            for filename in os.listdir(word_dir):
                filepath = os.path.join(word_dir, filename)
                if os.path.isfile(filepath) and os.path.getsize(filepath) < 5:
                    os.unlink(filepath)
                    cleaned_count += 1
                    self.logger.info(f"清理空文件: {filename}")
            
            return {
                "status": "success",
                "cleaned_files": cleaned_count,
                "directory": word_dir
            }
        except Exception as e:
            self.logger.error(f"清理空文件时出错: {e}")
            return {"status": "error", "error": str(e)}

    def get_crawler_config(self):
        """
        获取爬虫配置信息
        
        Returns:
            配置信息字典
        """
        return {
            "time_sleep": self.time_sleep,
            "per_page": self.__per_page,
            "headers": self.headers,
            "timeout": timeout
        }

    def update_crawler_config(self, **kwargs):
        """
        更新爬虫配置
        
        Args:
            **kwargs: 配置参数
            
        Returns:
            更新结果
        """
        try:
            if 'time_sleep' in kwargs:
                self.time_sleep = kwargs['time_sleep']
            if 'per_page' in kwargs:
                self.__per_page = kwargs['per_page']
            
            self.logger.info(f"更新爬虫配置: {kwargs}")
            return {"status": "success", "updated_config": kwargs}
        except Exception as e:
            self.logger.error(f"更新爬虫配置时出错: {e}")
            return {"status": "error", "error": str(e)}


def main():
    """主函数 - 测试百度爬虫"""
    try:
        print("🚀 开始测试百度爬虫...")
        
        # 创建爬虫实例
        crawler = BaiduCrawler(t=0.1)
        
        # 测试单个关键词下载
        test_query = "cat"
        print(f"🔍 测试关键词: {test_query}")
        
        crawler.start(test_query, 1, 1, 10)
        
        # 测试批量下载
        print(f"\n🔄 测试批量下载...")
        test_queries = ["cat", "dog"]
        results = crawler.batch_download(test_queries, 1)
        
        print("批量下载结果:")
        for query, result in results.items():
            if query != "summary":
                status = "✅" if result.get("status") == "success" else "❌"
                print(f"{status} {query}: {result}")
        
        if "summary" in results:
            summary = results["summary"]
            print(f"\n📊 总结: 处理 {summary['total_queries']} 个关键词, "
                  f"成功 {summary['success_count']} 个, "
                  f"耗时 {summary['total_time']:.2f} 秒")
        
        print("\n🎉 测试完成！")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")


if __name__ == '__main__':
    main()


# if __name__ == '__main__':
#     if len(sys.argv) > 1:
#         parser = argparse.ArgumentParser()
#         parser.add_argument("-w", "--word", type=str, help="抓取关键词", required=True)
#         parser.add_argument("-tp", "--total_page", type=int, help="需要抓取的总页数", required=True)
#         parser.add_argument("-sp", "--start_page", type=int, help="起始页数", required=True)
#         parser.add_argument("-pp", "--per_page", type=int, help="每页大小", choices=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100], default=30, nargs='?')
#         parser.add_argument("-d", "--delay", type=float, help="抓取延时（间隔）", default=0.05)
#         args = parser.parse_args()

#         crawler = BaiduCrawler(args.delay)
#         crawler.start(args.word, args.total_page, args.start_page, args.per_page)  # 抓取关键词为 “美女”，总数为 1 页（即总共 1*60=60 张），开始页码为 2
#     else:
#         # 如果不指定参数，那么程序会按照下面进行执行
#         crawler = BaiduCrawler(0.05)  # 抓取延迟为 0.05

#         crawler.start('美女', 1, 1, 10)  # 抓取关键词为 “美女”，总数为 1 页，开始页码为 2，每页30张（即总共 2*30=60 张）
#         # crawler.start('二次元 美女', 10, 1)  # 抓取关键词为 “二次元 美女”
#         # crawler.start('帅哥', 5)  # 抓取关键词为 “帅哥”