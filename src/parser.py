"""HTML内容解析器"""

from bs4 import BeautifulSoup
import re


class WeixinParser:
    """微信文章内容解析器"""
    
    def parse(self, html: str, url: str) -> dict:
        """
        解析微信文章HTML
        
        Args:
            html: 页面HTML内容
            url: 文章URL
            
        Returns:
            dict: 解析后的结构化数据
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取标题
        title_elem = soup.find('h1', {'id': 'activity-name'})
        title = title_elem.get_text(strip=True) if title_elem else "未找到标题"
        
        # 提取作者
        author_elem = soup.find('span', {'id': 'js_author_name'}) or \
                     soup.find('a', {'id': 'js_name'})
        author = author_elem.get_text(strip=True) if author_elem else "未知作者"
        
        # 提取发布时间
        time_elem = soup.find('em', {'id': 'publish_time'})
        publish_time = time_elem.get_text(strip=True) if time_elem else "未知时间"
        
        # 提取正文内容
        content_elem = soup.find('div', {'id': 'js_content'})
        content = self._clean_content(content_elem) if content_elem else "未找到正文内容"
        
        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content
        }
    
    def _clean_content(self, content_elem) -> str:
        """
        清理正文内容
        
        Args:
            content_elem: BeautifulSoup元素
            
        Returns:
            str: 清理后的纯文本内容
        """
        # 移除script和style标签
        for tag in content_elem.find_all(['script', 'style']):
            tag.decompose()
        
        # 获取文本内容
        text = content_elem.get_text(separator='\n', strip=True)
        
        # 清理多余空白
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()

